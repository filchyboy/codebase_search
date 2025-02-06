import subprocess
import shlex

# Define the base directory for search
BASE_DIR = "/Users/malevich/Repos/swingcity-dashboard"

# Define the grep command options
GREP_OPTIONS = '--exclude="*.md" --exclude-dir={node_modules,dist,vendor,filament,guides,logs,storage,docs,database}'

def main():
    print("Simple Grep CLI. Type your search term and press Enter.")
    print("Press Ctrl+C to exit.\n")
    
    while True:
        try:
            # Get user input for the search term
            search_term = input("Search: ").strip()
            if not search_term:
                continue  # Skip empty inputs
            
            # Escape special characters in the search term
            safe_search_term = shlex.quote(search_term)

            # Construct the full grep command
            command = f'grep -rHn {safe_search_term} {GREP_OPTIONS} {BASE_DIR}'

            # Execute the command using subprocess
            result = subprocess.run(command, shell=True, text=True, capture_output=True)

            # Display the results
            if result.stdout:
                print(result.stdout)
            else:
                print("No results")

        except KeyboardInterrupt:
            print("\nExiting Grep CLI.")
            break

if __name__ == "__main__":
    main()