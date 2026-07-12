#!/usr/bin/env python3

# DEPENDENCIES: gitpython

import os
import sys
import difflib
import unicodedata
from pathlib import Path
from xml.etree import ElementTree
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from logging import getLogger, Logger, StreamHandler, Formatter, INFO, CRITICAL, DEBUG

from git import Repo

SHOW_FIX_DETAILS = False  # Switch temorarily between INFO and DEBUG at the core fixing part


class LoggerWrapper:
    def __init__(self, logger: Logger | None = None, *, level: int = INFO) -> None:
        if logger is None:
            logger = getLogger(__name__)
            logger.setLevel(level)

            if not logger.handlers:
                handler = StreamHandler(sys.stdout)
                handler.setFormatter(Formatter("%(message)s"))
                handler.terminator = ""
                logger.addHandler(handler)
                logger.propagate = False

        self._logger = logger

    def log(self, level: int, *args, sep: str = " ", end: str = "\n", flush: bool = False):
        if self._logger.isEnabledFor(level):
            message = sep.join(map(str, args)) + end
            self._logger.log(level, message)
            if flush:
                for handler in self._logger.handlers:
                    handler.flush()

    @contextmanager
    def temporary_level(self, level: int):
        old_level = self._logger.level
        self._logger.setLevel(level)
        try:
            yield
        finally:
            self._logger.setLevel(old_level)

    def __getattr__(self, name):
        return getattr(self._logger, name)


class GitHistory:
    def __init__(self, repo_root):
        self._repo_root = Path(repo_root).resolve()
        self.repo = Repo(self._repo_root, search_parent_directories=True)

    def revisions(self, filename):
        """
        Newest -> oldest commits affecting this file. Follows renames.
        """
        shas = self.repo.git.log('--follow', '--format=%H', 'HEAD', '--', str(filename))

        for sha in shas.splitlines():
            commit_obj = self.repo.commit(sha)
            msg = commit_obj.message
            if msg is None:
                msg = 'No commit message'

            yield commit_obj, sha, msg

    def read_bytes(self, commit, filename):
        if isinstance(commit, str):
            commit = self.repo.commit(commit)

        tree = commit.tree
        if tree is None:
            raise ValueError('Commit object does not have tree!')

        blob = tree / str(filename)
        return blob.data_stream.read()

    def apply_patch_to_index(self, commit, patch_text, path):
        with NamedTemporaryFile() as index:
            # Redirect index to make isolated operations
            env = os.environ.copy()
            env['GIT_INDEX_FILE'] = index.name

            # Populate index with old commit
            self.repo.git.read_tree(commit.hexsha, env=env)

            # Open patch file
            patch_file = NamedTemporaryFile(mode='w', encoding='UTF-8', delete=False)
            try:
                # Write patch
                patch_file.write(patch_text)
                patch_file.close()

                # Apply patch
                self.repo.git.apply('--cached', patch_file.name, env=env)
                # Read the patched file
                blob = self.repo.git.show(f':{path}', env=env)
                patched_file_text = blob.encode('UTF-8')

            finally:
                os.unlink(patch_file.name)

            return patched_file_text

    def save_fixed_version(self, commit, original_path, fixed_bytes, log):
        original_path = Path(original_path)

        # Read original file from the specified commit
        orig_bytes = (commit.tree / original_path.as_posix()).data_stream.read()

        if orig_bytes == fixed_bytes:
            log.log(DEBUG, f'No real change for: {original_path}')

        # Preserve directory hierarchy
        out_dir = self._repo_root / original_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        # Save the fixed version to the original path
        fixed_file = out_dir / original_path.name
        fixed_file.write_bytes(fixed_bytes)
        self.repo.index.add([fixed_file])

    def save_commit_message(self, message):
        commit_editmsg = Path(self.repo.git_dir) / 'COMMIT_EDITMSG'
        commit_editmsg.write_text(message, encoding='UTF-8')


def parse_xml(text):
    try:
        ElementTree.fromstring(text)
        return True, None
    except ElementTree.ParseError as e:
        return False, str(e)


def strip_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def character_context(text, index):
    """
    Return the surrounding context of a character
    The initial context boundaries are the nearest non-alphanumeric characters on both sides
    If the result is only one character long, include one additional word on each side
    """

    start = index
    end = index + 1

    # Determine left context
    while start > 0 and text[start - 1].isalnum():
        start -= 1

    # Determine right context
    while end < len(text) and text[end].isalnum():
        end += 1

    # If the context is only a single character, expand to include neighboring words
    if end - start == 1:

        # Expand left over the separator
        left = start
        while left > 0 and not text[left - 1].isalnum():
            left -= 1

        # Include the word
        while left > 0 and text[left - 1].isalnum():
            left -= 1

        # Expand right over the separator
        right = end
        while right < len(text) and not text[right].isalnum():
            right += 1

        # Include the word
        while right < len(text) and text[right].isalnum():
            right += 1

        start = left
        end = right

    return text[start:end]


class XmlRepairer:
    def __init__(self, repo_root, log):
        self._repo_root = Path(repo_root).resolve()
        self._git = GitHistory(self._repo_root)
        self._logger = log
        if self._git.repo.is_dirty(untracked_files=True):
            self._logger.log(CRITICAL, 'Please use clean git working directory!')
            exit(1)

    def save_commit_message(self, message):
        self._git.save_commit_message(message)

    def process(self, commit_before_the_fix, filename: Path, fix_lvl):
        # Relativise path for git
        repo_relative_path = Path(filename).resolve().relative_to(self._repo_root)

        # Read file in bytes format at the starting commit
        current_bytes = self._git.read_bytes(commit_before_the_fix, repo_relative_path)

        # Parsing test
        ok, error = parse_xml(current_bytes)
        if ok:
            self._logger.log(INFO, 'OK', flush=True)  # OK in the same line
            return None

        with self._logger.temporary_level(fix_lvl):
            self._logger.log(DEBUG, '', flush=True)  # Newline character for later prints

        # Find the last revision where the file changed
        revisions_it = self._git.revisions(repo_relative_path)
        last_rev_commit, *_ = next(revisions_it, None)
        if last_rev_commit is None:
            raise ValueError('No file found in commits!')

        # Continue iteration on commits that changed the current file
        for commit, hexsha, msg in revisions_it:
            # Classify changes to find the erroneous commit
            classification, fixed_bytes = self._classify_revision(commit, last_rev_commit, repo_relative_path, fix_lvl)
            self._logger.log(INFO, classification, hexsha, msg.strip().replace('\n', ' '))
            # Found the erroneous commit
            if classification.startswith('valid_xml'):
                if classification == 'valid_xml_other_changes':
                    # Found the right commit, save fix and go to the next file
                    self._git.save_fixed_version(commit, repo_relative_path, fixed_bytes, self._logger)
                return commit, repo_relative_path

        return None

    def _classify_revision(self, commit, last_rev_commit, repo_relative_path, fix_level=INFO):
        historical_bytes = self._git.read_bytes(commit, repo_relative_path)

        # Parse test
        parses, _ = parse_xml(historical_bytes)
        if not parses:
            # Historical revision still broken
            return 'broken_other', None

        # Ask Git for the actual patch
        diff = commit.diff(last_rev_commit, paths=repo_relative_path, create_patch=True)

        # Make a real path file text (GitPython ommits the header)
        patch_text = f'--- a/{repo_relative_path}\n+++ b/{repo_relative_path}\n' \
                     + ''.join(item.diff.decode('UTF-8', errors='replace') for item in diff)

        with self._logger.temporary_level(fix_level):
            # Create filtered patch (we currently not check if there are other changes or not)
            filtered_patch = self._repair_patch_to_file(patch_text)

            # Apply filtered patch and test parsing
            filtered_bytes = self._git.apply_patch_to_index(commit, filtered_patch, repo_relative_path)
            parses, err = parse_xml(filtered_bytes)
            if not parses:
                raise Exception(err)

        return 'valid_xml_other_changes', filtered_bytes

    def _repair_patch_to_file(self, patch_text):
        """
        Apply a git patch while repairing encoding corruption.
        The patch must describe a change from the old file version to the new file version
        """
        repaired_lines = []
        current_hunk: list[str] | None = None

        # Split to lines platform-independently (splitlines() not work as it split on other control characters too)
        for line in patch_text.replace('\r\n', '\n').split('\n'):
            # Ignore patch headers
            if line.startswith('diff --git') or line.startswith('index ') or line.startswith('--- ') \
                    or line.startswith('+++ '):
                repaired_lines.append(line)
                continue

            # Start a new hunk
            if line.startswith('@@'):
                if current_hunk is not None:
                    repaired_lines.extend(self._repair_hunk(current_hunk))
                current_hunk = [line]
                continue

            # Ignore lines before first hunk
            if current_hunk is None:
                continue

            current_hunk.append(line)

        # Final hunk
        if current_hunk is not None:
            repaired_lines.extend(self._repair_hunk(current_hunk))

        return '\n'.join(repaired_lines)

    def _repair_hunk(self, hunk):
        """
        Returns repaired hunks
        A hunk may contain several replacement groups separated by context lines
        """
        removed = []
        added = []

        # Drop only the trailing empty line caused by a final '\n'
        add_final_empty_line = False
        hunk_last_index = None
        if hunk and hunk[-1] == '':
            hunk_last_index = -1
            add_final_empty_line = True

        # Skip checking the @@ header and put it directly into the output
        repaired_hunk = [hunk[0]]
        meta_add = []
        meta_remove = []
        last = ''
        for line in hunk[1:hunk_last_index]:
            if line.startswith(' '):
                # Context separates replacement groups
                if added or removed:
                    # Repair block and add the result (lines to remove and to add) separately
                    lines_remove, lines_add = self._repair_block(removed, added)
                    repaired_hunk.extend(lines_remove)
                    repaired_hunk.extend(lines_add)
                    removed.clear()
                    added.clear()

                repaired_hunk.append(line)  # Append unchanged line
                last = ' '

            elif line.startswith('-'):
                removed.append(line[1:])
                last = '-'

            elif line.startswith('+'):
                added.append(line[1:])
                last = '+'

            elif line.startswith('\\ '):  # Metadata, store separately
                # We want to have newline at the end so do not add it to the repaired hunk
                if last == '-':
                    meta_remove.append(line)  # E.g. There was no newline at the end
                elif last == '+':
                    meta_add.append(line)  # E.g. There is currently no newline at the end
                else:
                    raise NotImplementedError('This should not happen!')
            else:
                raise ValueError(f'Unexpected diff line: {line!r}')

        # Final replacement group
        if added or removed:
            lines_remove, lines_add = self._repair_block(removed, added)
            repaired_hunk.extend(lines_remove)
            repaired_hunk.extend(meta_remove)

            repaired_hunk.extend(lines_add)
            repaired_hunk.extend(meta_add)

        if add_final_empty_line:
            repaired_hunk.append('')  # For later ''.join(...) to have a final newline
        return repaired_hunk

    def _repair_block(self, removed_lines, added_lines):
        """
        Returns the repaired lines with meaningful changes and without encoding corruption
        removed_lines : list[str] Consecutive deleted lines
        added_lines : list[str] Consecutive added_lines lines
        """
        lines_remove = []
        lines_add = []
        # Pure insertion/deletion
        if len(removed_lines) != len(added_lines):
            # Safety measure if we would exhibit such change
            self._logger.log(CRITICAL, 'TODO PURE INSERTION/DELETION NOT IMPLEMENTED!')
            # Cannot safely pair lines. Keep original patch block
            for line in removed_lines:
                lines_remove.append('-' + line)

            for line in added_lines:
                lines_add.append('+' + line)

            return lines_remove, lines_add

        # Pair replacements line-by-line
        for old, new in zip(removed_lines, added_lines):
            repaired_line = self._check_changes_by_line(old, new)
            lines_remove.append('-' + old)
            # It is ok, if old and repaired_line is the same. We keep them because of the hunk header
            lines_add.append('+' + repaired_line)

        return lines_remove, lines_add

    def _check_changes_by_line(self, old_line, new_line):
        """
        Examine lines and keep non-accented character changes while omiting the encoding errors
        This function contains specific stuff
        """
        out = []
        matcher = difflib.SequenceMatcher(None, old_line, new_line)
        for tag, a1, a2, b1, b2 in matcher.get_opcodes():

            left = old_line[a1:a2]
            right = new_line[b1:b2]

            if tag == 'equal':
                out.append(left)
                continue

            # Length changes mean insertions/deletions
            # Those are containng also real changes, not (just) encoding corruption
            if len(left) != len(right):
                if left == '🙂' and right == '=B':  # SLIGHTLY SMILING FACE
                    self._logger.log(DEBUG, f'Known corrupted encoding (multichar): {left!r} -> {right!r}')
                    out.append(left)
                    continue
                # no -> both, no -> right, no -> left,
                # right -> no, right -> both
                # left ->right, left -> both, left -> both, left -> no
                if (left == '' and right == 'th') or (left == 'no' and right == 'right') \
                        or (left == 'no' and right == 'left') \
                        or (left == 'right' and right == 'no') or (left == 't' and right == '') \
                        or (left == 'lef' and right == 'righ') or (left == 'lef' and right == 'bo') \
                        or (left == '' and right == 'h') or (left == 'left' and right == 'no'):
                    out.append(right)
                    continue

                self._logger.log(DEBUG, f'UNKnown replace: {left!r} -> {right!r},'
                                        f' context={character_context(old_line, a1)!r}')
                out.append(right)
                continue

            # Check characterwise
            for offset, (x, y) in enumerate(zip(left, right)):
                keep_orig_character = self._classify_character_pairs(old_line, a1, offset, x, y)
                if keep_orig_character:
                    out.append(x)
                else:
                    out.append(y)

        return ''.join(out)

    def _classify_character_pairs(self, old, a1, offset, x, y):
        old_index = a1 + offset

        if x == y:
            return False

        # Case 1:
        # Original character was non-ASCII and became replacement char
        if ord(x) > 127 and y in {'\ufffd', '?'}:
            self._logger.log(DEBUG, f'Known corrupted encoding: {x!r} -> {y!r},'
                                    f' context={character_context(old, old_index)!r}')
            return True

        # Case 2:
        # Original character was non-ASCII and lost its accent
        if ord(x) > 127 and strip_accents(x) == y:
            self._logger.log(DEBUG, f'Known lost accent: {x!r} -> {y!r},'
                                    f' context={character_context(old, old_index)!r}')
            return True

        # Case 3:
        # Normalized Unicode forms differ but base character is same
        if strip_accents(x) == strip_accents(y):
            self._logger.log(DEBUG, f'Known normalised accent eq.: {x!r} -> {y!r},'
                                    f' context={character_context(old, old_index)!r}')
            return True

        # Case 4:
        # ő -> Q, Ő -> P, ű -> q, Ű -> p don't know how but it is there
        if (x == 'ő' and y == 'Q') or (x == 'ű' and y == 'q') or (x == 'Ő' and y == 'P') or \
                (x == 'Ű' and y == 'p'):
            self._logger.log(DEBUG, f'Known corruption: {x!r} -> {y!r},'
                                    f' context={character_context(old, old_index)!r}')
            return True

        # Case 5:
        # : -> › (SINGLE RIGHT-POINTING ANGLE QUOTATION MARK) as part of POS tag don't know how but it is there
        if x == '›' and y == ':':
            self._logger.log(DEBUG, f'Known corruption: {x!r} -> {y!r},'
                                    f' context={character_context(old, old_index)!r}')
            return True

        # Case 6:
        # – -> \x13 (EN DASH) don't know how but it is there
        if x == '–' and y == '\x13':
            self._logger.log(DEBUG, f'Known corruption: {x!r} -> {y!r},'
                                    f' context={character_context(old, old_index)!r}')
            return True

        # Case 6:
        # … -> & (HORIZONTAL ELLIPSIS) don't know how but it is there
        if x == '…' and y == '&':
            self._logger.log(DEBUG, f'Known corruption: {x!r} -> {y!r},'
                                    f' context={character_context(old, old_index)!r}')
            return True

        # Case 7:
        # „ -> \x1e (DOUBLE LOW-9 QUOTATION MARK, Record Separator) don't know how but it is there
        if x == '„' and y == '\x1e':
            self._logger.log(DEBUG, f'Known corruption: {x!r} -> {y!r},'
                                    f' context={character_context(old, old_index)!r}')
            return True

        # Case 8:
        # ” -> \x1d (RIGHT DOUBLE QUOTATION MARK, Group Separator) don't know how but it is there
        if x == '”' and y == '\x1d':
            self._logger.log(DEBUG, f'Known corruption: {x!r} -> {y!r},'
                                    f' context={character_context(old, old_index)!r}')
            return True

        # right -> both, no -> both
        if (x == 'r' and y == 'b') or (x == 'i' and y == 'o') or (x == 'g' and y == 't') or (x == 'n' and y == 'b'):
            return False

        self._logger.log(DEBUG, f'UNKnown corruption: {x!r} -> {y!r},'
                                f' context={character_context(old, old_index)!r}')
        return False


def main():
    log = LoggerWrapper()
    repo_root = '..'
    repairer = XmlRepairer(repo_root, log)

    if SHOW_FIX_DETAILS:
        fix_level = DEBUG
    else:
        fix_level = INFO

    base_commit = '9645db3172b3dfbacc493724f6127c8f27008e1e'
    commit_message = ['Reproducible fix for files with messed up encoding',
                      'Reproduce with script/fix_encoding.py',
                      'To show real differences without the encoding errors issue the folowing commands:']
    for filename in iter_xml_files('../corpus/Morph annotated'):
        log.log(INFO, f'Checking {filename} ', end='')
        res = repairer.process(base_commit, filename, fix_level)
        if res is not None:
            commit, repo_relative_path = res
            commit_message.append(f'git diff {commit.hexsha} THIS_COMMIT_SHA -- "{repo_relative_path}"')

    repairer.save_commit_message('\n'.join(commit_message) + '\n')
    log.log(INFO, 'Changes are staged and .git/COMMIT_EDITMSG is prepared')
    log.log(INFO, 'Commit then issue `git commit --amend --no-edit` to fix git wrong diffs')
    log.log(INFO, 'Done')


def iter_xml_files(directory):
    directory = Path(directory)

    if not directory.is_dir():
        raise NotADirectoryError(directory)

    yield from sorted(directory.glob('**/*.xml'))


if __name__ == '__main__':
    main()
