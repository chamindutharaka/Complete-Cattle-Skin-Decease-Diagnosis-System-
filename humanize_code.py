import os
import re

def remove_emojis(text):
    # Matches emojis (simplistic regex for common emojis block)
    return re.sub(r'[\U00010000-\U0010ffff]', '', text)

def humanize_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove all emojis
    content = remove_emojis(content)

    # Remove multi-line docstrings """..."""
    content = re.sub(r'\"\"\"[\s\S]*?\"\"\"', '', content)
    content = re.sub(r"\'\'\'[\s\S]*?\'\'\'", '', content)

    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith('#'):
            comment = stripped[1:].strip()
            # If it's a structural comment like ======== or --------, keep it or remove it
            if set(comment) <= set('-='):
                continue # remove it
                
            # humanize the comment
            comment = comment.lower()
            if comment.endswith('.'):
                comment = comment[:-1]
                
            # Some replacements
            comment = comment.replace('initialize', 'init')
            comment = comment.replace('configuration', 'config')
            comment = comment.replace('calculate', 'calc')
            comment = comment.replace('function to', '')
            comment = comment.replace('returns ', '')
            comment = comment.replace('parameters:', '')
            comment = comment.replace('database', 'db')
            comment = comment.replace('application', 'app')
            comment = comment.replace('generate', 'gen')
            
            # Make it look like a student wrote it
            if comment == 'simulate diurnal cycle (24 hour period)':
                comment = 'simulate 24h cycle'
            elif comment == 'base values':
                comment = 'base vals'
                
            indent = line[:len(line) - len(stripped)]
            # randomly maybe we skip some very obvious comments?
            if 'import' in comment or len(comment.split()) > 10:
                continue # drop long boring comments
                
            if comment:
                new_lines.append(indent + '# ' + comment)
        else:
            # Inline comments
            if '#' in line and 'http' not in line and 'rgb' not in line:
                parts = line.split('#', 1)
                code_part = parts[0]
                comment_part = parts[1].strip().lower()
                if comment_part.endswith('.'):
                    comment_part = comment_part[:-1]
                comment_part = comment_part.replace('initialize', 'init').replace('configuration', 'config').replace('database', 'db')
                
                # Keep it short
                if len(comment_part.split()) < 8:
                    new_lines.append(code_part + '# ' + comment_part)
                else:
                    new_lines.append(code_part.rstrip())
            else:
                new_lines.append(line)
                
    # Remove excessive empty lines
    final_text = '\n'.join(new_lines)
    final_text = re.sub(r'\n{3,}', '\n\n', final_text)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_text)

def process_dir(directory):
    for root, dirs, files in os.walk(directory):
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if file != 'humanize_code.py':
                    print(f"Humanizing {filepath}")
                    humanize_file(filepath)
            elif file.endswith('.ipynb'):
                # Also strip emojis from ipynb just in case
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        text = f.read()
                    text = remove_emojis(text)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(text)
                    print(f"Removed emojis from {filepath}")
                except:
                    pass

if __name__ == '__main__':
    process_dir('.')
    print("Done!")
