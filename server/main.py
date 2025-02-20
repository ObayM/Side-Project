import argparse
import os
import shutil
import webbrowser
# from pytube import YouTube
# from fpdf import FPDF
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from zipfile import ZipFile
# from PIL import Image
import subprocess


# Define functions for the tasks

def move_files_by_type(src_folder, dest_folder, file_extension):
    """Moves files of a specific type from source to destination."""
    try:
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
        for file in os.listdir(src_folder):
            if file.endswith(file_extension):
                shutil.move(os.path.join(src_folder, file), os.path.join(dest_folder, file))
        print(f"Moved all {file_extension} files to {dest_folder}.")
    except Exception as e:
        print(f"Error moving files: {str(e)}")

def organize_desktop(desktop_path=os.path.expanduser("~/Desktop")):
    """Organizes desktop files by type."""
    try:
        file_types = {
            "Documents": [".pdf", ".docx", ".txt"],
            "Images": [".jpg", ".png", ".gif"],
            "Videos": [".mp4", ".mkv"],
            "Archives": [".zip", ".rar"]
        }
        for category, extensions in file_types.items():
            category_path = os.path.join(desktop_path, category)
            os.makedirs(category_path, exist_ok=True)
            for file in os.listdir(desktop_path):
                if any(file.endswith(ext) for ext in extensions):
                    shutil.move(os.path.join(desktop_path, file), os.path.join(category_path, file))
        print("Desktop organized successfully.")
    except Exception as e:
        print(f"Error organizing desktop: {str(e)}")

def search_google(query):
    """Searches Google with the given query."""
    webbrowser.open(f"https://www.google.com/search?q={query}")
    print(f"Searched Google for: {query}")

def download_youtube_video(url, save_path="."):
    """Downloads a YouTube video to the specified path."""
    try:
        yt = YouTube(url)
        stream = yt.streams.get_highest_resolution()
        stream.download(output_path=save_path)
        print(f"Downloaded video: {yt.title}")
    except Exception as e:
        print(f"Error downloading video: {str(e)}")

def batch_rename_files(folder_path, prefix):
    """Renames all files in a folder with a given prefix."""
    try:
        for i, file in enumerate(os.listdir(folder_path)):
            ext = os.path.splitext(file)[1]
            new_name = f"{prefix}_{i+1}{ext}"
            os.rename(os.path.join(folder_path, file), os.path.join(folder_path, new_name))
        print("Batch rename completed.")
    except Exception as e:
        print(f"Error renaming files: {str(e)}")

def zip_folder(folder_path, zip_name):
    """Creates a ZIP file from a folder."""
    try:
        with ZipFile(f"{zip_name}.zip", 'w') as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    zipf.write(os.path.join(root, file))
        print(f"Folder {folder_path} zipped successfully as {zip_name}.zip.")
    except Exception as e:
        print(f"Error creating ZIP: {str(e)}")

def extract_zip(zip_path, dest_folder):
    """Extracts a ZIP file."""
    try:
        with ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(dest_folder)
        print(f"Extracted {zip_path} to {dest_folder}.")
    except Exception as e:
        print(f"Error extracting ZIP: {str(e)}")

def convert_to_pdf(files, output_pdf):
    """Converts files to a PDF."""
    try:
        pdf = FPDF()
        for file in files.split(","):
            if file.endswith(".txt"):
                with open(file, "r") as f:
                    pdf.add_page()
                    for line in f:
                        pdf.set_font("Arial", size=12)
                        pdf.cell(0, 10, line.strip(), ln=True)
            elif file.endswith((".jpg", ".png")):
                pdf.add_page()
                pdf.image(file, x=10, y=10, w=190)
        pdf.output(output_pdf)
        print(f"PDF created: {output_pdf}")
    except Exception as e:
        print(f"Error creating PDF: {str(e)}")

def send_email(sender_email, sender_password, recipient_email, subject, message):
    """Sends an email with the specified content."""
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

def open_website(url):
    """Opens a website in the default browser."""
    webbrowser.open(url)
    print(f"Opened website: {url}")

def shutdown_computer():
    """Shuts down the computer."""
    try:
        if os.name == 'nt':  # For Windows
            subprocess.run(["shutdown", "/s", "/f", "/t", "1"])
        elif os.name == 'posix':  # For macOS or Linux
            subprocess.run(["shutdown", "-h", "now"])
        print("Computer is shutting down...")
    except Exception as e:
        print(f"Error shutting down: {str(e)}")

def restart_computer():
    """Restarts the computer."""
    try:
        if os.name == 'nt':  # For Windows
            subprocess.run(["shutdown", "/r", "/f", "/t", "1"])
        elif os.name == 'posix':  # For macOS or Linux
            subprocess.run(["shutdown", "-r", "now"])
        print("Computer is restarting...")
    except Exception as e:
        print(f"Error restarting: {str(e)}")

def take_screenshot(save_path):
    """Takes a screenshot and saves it to the specified path."""
    try:
        screenshot = Image.grab()
        screenshot.save(save_path)
        print(f"Screenshot saved to {save_path}.")
    except Exception as e:
        print(f"Error taking screenshot: {str(e)}")

def create_folder(folder_name):
    """Creates a new folder with the specified name."""
    try:
        os.makedirs(folder_name, exist_ok=True)
        print(f"Folder created: {folder_name}")
    except Exception as e:
        print(f"Error creating folder: {str(e)}")

def delete_folder(folder_name):
    """Deletes the specified folder."""
    try:
        shutil.rmtree(folder_name)
        print(f"Folder deleted: {folder_name}")
    except Exception as e:
        print(f"Error deleting folder: {str(e)}")

def open_task_manager():
    """Opens Task Manager without requiring elevated privileges."""
    try:
        subprocess.run("taskmgr", shell=True)
        print("Task Manager opened successfully.")
    except Exception as e:
        print(f"Error opening task manager: {str(e)}")

def install_package(package_name):
    """Installs a Python package."""
    try:
        subprocess.run(["pip", "install", package_name])
        print(f"Package {package_name} installed successfully.")
    except Exception as e:
        print(f"Error installing package: {str(e)}")

def open_file_with_default_application(file_path):
    """Opens a file with the default application."""
    try:
        subprocess.run(["open", file_path]) if os.name == 'posix' else subprocess.run([file_path])
        print(f"Opened file: {file_path}")
    except Exception as e:
        print(f"Error opening file: {str(e)}")

def uninstall_package(package_name):
    """Uninstalls a Python package."""
    try:
        subprocess.run(["pip", "uninstall", "-y", package_name])
        print(f"Package {package_name} uninstalled successfully.")
    except Exception as e:
        print(f"Error uninstalling package: {str(e)}")
def create_and_write_file(content):
    """Creates a text file in the current directory and writes the provided content to it."""
    try:
        # Open the file in write mode ('w'). This will create the file in the current directory.
        with open('output.txt', 'w') as file:
            file.write(content)
        
        print("File created and content written.")
    except Exception as e:
        print(f"Error creating or writing to the file: {str(e)}")

# Command-line interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perform various PC tasks.")
    parser.add_argument("--action", help="The action to perform", required=True)
    parser.add_argument("--src_folder", help="Source folder path")
    parser.add_argument("--dest_folder", help="Destination folder path")
    parser.add_argument("--file_extension", help="File extension to filter (e.g., .txt, .jpg)")
    parser.add_argument("--query", help="Search query for Google")
    parser.add_argument("--url", help="YouTube video URL or website URL")
    parser.add_argument("--save_path", help="Path to save downloaded video or file")
    parser.add_argument("--folder_path", help="Folder path for renaming or zipping")
    parser.add_argument("--prefix", help="Prefix for renaming files")
    parser.add_argument("--zip_name", help="Name for the zip file")
    parser.add_argument("--files", help="Comma-separated list of files to convert to PDF")
    parser.add_argument("--sender_email", help="Sender email for sending email")
    parser.add_argument("--sender_password", help="Sender email password")
    parser.add_argument("--recipient_email", help="Recipient email address")
    parser.add_argument("--subject", help="Subject of the email")
    parser.add_argument("--message", help="Message body of the email")
    parser.add_argument("--folder_name", help="Folder name to create or delete")
    parser.add_argument("--file_path", help="File path to open with default application")
    parser.add_argument("--package_name", help="Package name to install/uninstall")
    parser.add_argument("--content", help="Content to write in the text file")

    args = parser.parse_args()

    # Execute actions based on the arguments provided
    if args.action == "move_files_by_type":
        move_files_by_type(args.src_folder, args.dest_folder, args.file_extension)
    elif args.action == "organize_desktop":
        organize_desktop()
    elif args.action == "search_google":
        search_google(args.query)
    elif args.action == "download_youtube_video":
        download_youtube_video(args.url, args.save_path)
    elif args.action == "batch_rename_files":
        batch_rename_files(args.folder_path, args.prefix)
    elif args.action == "zip_folder":
        zip_folder(args.folder_path, args.zip_name)
    elif args.action == "extract_zip":
        extract_zip(args.zip_name, args.dest_folder)
    elif args.action == "convert_to_pdf":
        convert_to_pdf(args.files, args.save_path)
    elif args.action == "send_email":
        send_email(args.sender_email, args.sender_password, args.recipient_email, args.subject, args.message)
    elif args.action == "open_website":
        open_website(args.url)
    elif args.action == "shutdown_computer":
        shutdown_computer()
    elif args.action == "restart_computer":
        restart_computer()
    elif args.action == "take_screenshot":
        take_screenshot(args.save_path)
    elif args.action == "create_folder":
        create_folder(args.folder_name)
    elif args.action == "delete_folder":
        delete_folder(args.folder_name)
    elif args.action == "open_task_manager":
        open_task_manager()
    elif args.action == "install_package":
        install_package(args.package_name)
    elif args.action == "open_file_with_default_application":
        open_file_with_default_application(args.file_path)
    elif args.action == "uninstall_package":
        uninstall_package(args.package_name)
    elif args.action == "create_and_write_file":
        create_and_write_file(args.content)
    else:
        print(f"Unknown action: {args.action}")
