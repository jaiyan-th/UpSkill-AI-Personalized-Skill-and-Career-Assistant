import os
import glob

def fix_datetime():
    files = glob.glob('c:/Users/jaiya/Documents/UpSkill AI-Skill Assistant/UpSkill AI-Skill Assistant/backend/app/**/*.py', recursive=True)
    count = 0
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            
            if "datetime('now'" in content:
                # Replace the two specific datetime strings
                new_content = content.replace("datetime('now', '-1 hour')", "NOW() - INTERVAL '1 hour'")
                new_content = new_content.replace("datetime('now')", "CURRENT_TIMESTAMP")
                
                if new_content != content:
                    with open(f, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    print(f"Updated {f}")
                    count += 1
        except Exception as e:
            print(f"Error reading {f}: {e}")
    
    print(f"Successfully updated {count} files.")

if __name__ == '__main__':
    fix_datetime()
