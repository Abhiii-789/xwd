import os
import sys
import time
import random
import string
import json
import requests
import threading
import socket
from functools import wraps
from pathlib import Path

# Global variables
stop_event = threading.Event()
active_task = None
TASK_FILE = 'waleed_tasks.json'
offline_mode = False

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': '/',
    'Accept-Language': 'en-US,en;q=0.9',
}

def is_connected():
    """Check if there's an active internet connection"""
    try:
        # Connect to a reliable host with a short timeout
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        pass
    return False

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_boxed_text(text, border_char="═", padding=1, color_code="\033[1;35m"):
    """Print text in a stylish box"""
    lines = text.split('\n')
    max_len = max(len(line) for line in lines)
    width = max_len + padding * 2
    
    top_border = color_code + "╔" + border_char * (width + 2) + "╗" + "\033[0m"
    bottom_border = color_code + "╚" + border_char * (width + 2) + "╝" + "\033[0m"
    
    print(top_border)
    for line in lines:
        padded_line = line.center(max_len)
        print(color_code + "║ " + "\033[0m" + padded_line + color_code + " ║" + "\033[0m")
    print(bottom_border)

def display_banner():
    banner = r"""
    $$$$$$\  $$$$$$$\  $$\   $$\ $$$$$$\  $$$$$$\  $$\   $$\  $$$$$$\  $$\   $$\ 
$$  __$$\ $$  __$$\ $$ |  $$ |\_$$  _|$$  __$$\ $$ |  $$ |$$ ___$$\ $$ | $$  |
$$ /  $$ |$$ |  $$ |$$ |  $$ |  $$ |  $$ /  \__|$$ |  $$ |\_/   $$ |$$ |$$  / 
\$$$$$$$ |$$$$$$$\ |$$$$$$$$ |  $$ |  \$$$$$$\  $$$$$$$$ |  $$$$$ / $$$$$  /  
 \____$$ |$$  __$$\ $$  __$$ |  $$ |   \____$$\ $$  __$$ |  \___$$\ $$  $$<   
$$\   $$ |$$ |  $$ |$$ |  $$ |  $$ |  $$\   $$ |$$ |  $$ |$$\   $$ |$$ |\$$\  
\$$$$$$  |$$$$$$$  |$$ |  $$ |$$$$$$\ \$$$$$$  |$$ |  $$ |\$$$$$$  |$$ | \$$\ 
 \______/ \_______/ \__|  \__|\______| \______/ \__|  \__| \______/ \__|  \__|
                                                                              
   POWER FULL DEVELOPING BY ABHII OFFLINE TOOL 😘
    """
    print_boxed_text(banner, "═", 1, "\033[1;35m")
    print("")

def print_menu_option(num, text, color="\033[1;32m"):
    """Print a menu option with stylish formatting"""
    print(f"{color}║ {num}. {text}\033[0m")

def print_section_header(text, color="\033[1;36m"):
    """Print a section header with stylish formatting"""
    width = len(text) + 4
    print(f"{color}╔{'═' * width}╗\033[0m")
    print(f"{color}║  {text}  ║\033[0m")
    print(f"{color}╚{'═' * width}╝\033[0m")

def print_status(message, status_type="info"):
    """Print status messages with colored formatting"""
    if status_type == "success":
        print(f"\033[1;32m[✓] {message}\033[0m")
    elif status_type == "error":
        print(f"\033[1;31m[✗] {message}\033[0m")
    elif status_type == "warning":
        print(f"\033[1;33m[!] {message}\033[0m")
    elif status_type == "info":
        print(f"\033[1;34m[ℹ] {message}\033[0m")
    else:
        print(f"[ ] {message}")

def fetch_profile_name(token):
    global offline_mode
    if offline_mode:
        return "OFFLINE MODE"
    
    try:
        res = requests.get(
            f'https://graph.facebook.com/me?access_token={token}',
            timeout=8
        )
        return res.json().get('name', 'Unknown')
    except Exception:
        return 'Unknown'

def send_messages_offline(tokens, thread_id, hater_name, delay, messages, task_id):
    """Send messages with offline capability"""
    global stop_event, offline_mode
    tok_i, msg_i = 0, 0
    total_tok, total_msg = len(tokens), len(messages)
    
    print_section_header("STARTING MESSAGE SENDING")
    print_status(f"Using {len(tokens)} tokens and {len(messages)} messages", "info")
    print_status(f"Delay between messages: {delay} seconds", "info")
    print_status("Press Ctrl+C to stop", "warning")
    print("")
    
    # Check initial connection
    if not is_connected():
        offline_mode = True
        print_status("No internet connection detected. Starting in OFFLINE MODE", "warning")
        print_status("Messages will be queued and sent when connection is restored", "warning")
        print("")
    
    # Queue for offline messages
    message_queue = []
    
    try:
        while not stop_event.is_set():
            # Check connection status
            current_connection = is_connected()
            if offline_mode and current_connection:
                print_status("Internet connection restored. Exiting OFFLINE MODE", "success")
                offline_mode = False
            elif not offline_mode and not current_connection:
                print_status("Internet connection lost. Entering OFFLINE MODE", "warning")
                offline_mode = True
            
            tk = tokens[tok_i]
            msg = messages[msg_i]
            full_msg = f"{hater_name} {msg}"
            
            if offline_mode:
                # Queue the message for later sending
                message_queue.append({
                    'token': tk,
                    'message': full_msg,
                    'timestamp': time.time()
                })
                print(f"\033[1;33m[⏳ QUEUED]\033[0m {full_msg[:40]}... via TOKEN-{tok_i+1} (Offline)")
            else:
                # Try to send the message
                try:
                    response = requests.post(
                        f'https://graph.facebook.com/v15.0/t_{thread_id}/',
                        data={'access_token': tk, 'message': full_msg},
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        print(f"\033[1;32m[✓ SENT]\033[0m {full_msg[:40]}... via TOKEN-{tok_i+1}")
                    else:
                        print(f"\033[1;31m[✗ ERROR {response.status_code}]\033[0m Failed to send message via TOKEN-{tok_i+1}")
                        # Add to queue if there's an error (might be connection issue)
                        message_queue.append({
                            'token': tk,
                            'message': full_msg,
                            'timestamp': time.time()
                        })
                        
                except Exception as e:
                    print(f"\033[1;31m[✗ ERROR]\033[0m {e}")
                    offline_mode = True
                    message_queue.append({
                        'token': tk,
                        'message': full_msg,
                        'timestamp': time.time()
                    })
            
            # Process message queue if we have connection
            if not offline_mode and message_queue:
                print_status(f"Processing {len(message_queue)} queued messages", "info")
                successful_sends = []
                
                for i, queued_msg in enumerate(message_queue):
                    try:
                        response = requests.post(
                            f'https://graph.facebook.com/v15.0/t_{thread_id}/',
                            data={'access_token': queued_msg['token'], 'message': queued_msg['message']},
                            headers=headers,
                            timeout=15
                        )
                        
                        if response.status_code == 200:
                            print(f"\033[1;32m[✓ SENT QUEUED]\033[0m {queued_msg['message'][:40]}...")
                            successful_sends.append(i)
                        else:
                            print(f"\033[1;31m[✗ ERROR {response.status_code}]\033[0m Failed to send queued message")
                            
                    except Exception as e:
                        print(f"\033[1;31m[✗ ERROR]\033[0m {e}")
                        # Keep in queue if failed
                
                # Remove successfully sent messages from queue
                message_queue = [msg for i, msg in enumerate(message_queue) if i not in successful_sends]
                
                if message_queue:
                    print_status(f"{len(message_queue)} messages remain in queue", "warning")
                else:
                    print_status("All queued messages sent successfully", "success")
            
            tok_i = (tok_i + 1) % total_tok
            msg_i = (msg_i + 1) % total_msg
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print("\n[!] Stopping message sending...")
        if message_queue:
            print_status(f"{len(message_queue)} messages remain in queue", "warning")
        stop_event.set()

def save_task(task_id, task_info):
    tasks = {}
    if os.path.exists(TASK_FILE):
        with open(TASK_FILE, 'r') as f:
            tasks = json.load(f)
    
    tasks[task_id] = task_info
    with open(TASK_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)

def load_tasks():
    if not os.path.exists(TASK_FILE):
        return {}
    
    with open(TASK_FILE, 'r') as f:
        return json.load(f)

def delete_task(task_id):
    tasks = load_tasks()
    if task_id in tasks:
        del tasks[task_id]
        with open(TASK_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)
        return True
    return False

def start_new_task():
    global stop_event, active_task
    
    print_section_header("STARTING NEW TASK")
    
    # Token option
    token_option = input("\033[1;36m║ Token option (1 - Single token, 2 - Multiple tokens from file): \033[0m").strip()
    
    tokens = []
    if token_option == "1":
        token = input("\033[1;36m║ Enter Facebook token: \033[0m").strip()
        if token:
            tokens = [token]
    elif token_option == "2":
        token_file = input("\033[1;36m║ Enter path to tokens file: \033[0m").strip()
        try:
            with open(token_file, 'r') as f:
                tokens = [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            print_status(f"Error reading tokens file: {e}", "error")
            return
    else:
        print_status("Invalid option", "error")
        return
    
    if not tokens:
        print_status("No tokens provided", "error")
        return
    
    # Thread ID
    thread_id = input("\033[1;36m║ Enter Thread ID: \033[0m").strip()
    if not thread_id:
        print_status("Thread ID is required", "error")
        return
    
    # Hater name
    hater_name = input("\033[1;36m║ Enter Hater Name: \033[0m").strip()
    if not hater_name:
        print_status("Hater name is required", "error")
        return
    
    # Delay
    try:
        delay = int(input("\033[1;36m║ Enter delay between messages (seconds): \033[0m").strip() or "1")
    except ValueError:
        print_status("Invalid delay, using 1 second", "warning")
        delay = 1
    
    # Messages file
    msg_file = input("\033[1;36m║ Enter path to messages file: \033[0m").strip()
    try:
        with open(msg_file, 'r', encoding='utf-8', errors='ignore') as f:
            messages = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print_status(f"Error reading messages file: {e}", "error")
        return
    
    if not messages:
        print_status("No messages found in file", "error")
        return
    
    # Generate task ID
    task_id = 'waleed_' + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    
    # Start the sending thread
    stop_event = threading.Event()
    thread = threading.Thread(
        target=send_messages_offline,
        args=(tokens, thread_id, hater_name, delay, messages, task_id),
        daemon=True
    )
    
    # Save task info
    task_info = {
        'name': hater_name,
        'token': tokens[0],
        'tokens_all': tokens,
        'fb_name': fetch_profile_name(tokens[0]),
        'thread_id': thread_id,
        'msg_file': msg_file,
        'msgs': messages,
        'delay': delay,
        'msg_count': len(messages),
        'status': 'ACTIVE',
        'start_time': time.time()
    }
    
    save_task(task_id, task_info)
    active_task = task_id
    
    print_section_header("TASK STARTED SUCCESSFULLY")
    print_status(f"Task ID: {task_id}", "info")
    print_status(f"Using {len(tokens)} tokens", "info")
    print_status(f"{len(messages)} messages loaded", "info")
    print_status(f"Delay: {delay} seconds", "info")
    print_status("OFFLINE MODE ENABLED - Will continue working without internet", "success")
    print_status("Press Ctrl+C to stop the task", "warning")
    print("")
    
    thread.start()
    
    try:
        while thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Stopping task...")
        stop_event.set()
        thread.join()
        
        # Update task status
        tasks = load_tasks()
        if task_id in tasks:
            tasks[task_id]['status'] = 'STOPPED'
            with open(TASK_FILE, 'w') as f:
                json.dump(tasks, f, indent=2)
        
        print_status("Task stopped", "info")

def view_tasks():
    tasks = load_tasks()
    if not tasks:
        print_status("No tasks found", "warning")
        return
    
    print_section_header("SAVED TASKS")
    
    for task_id, task_info in tasks.items():
        status = task_info.get('status', 'UNKNOWN')
        status_color = "\033[1;32m" if status == 'ACTIVE' else "\033[1;31m" if status == 'STOPPED' else "\033[1;33m"
        
        print(f"\033[1;36m╔{'═' * 78}╗\033[0m")
        print(f"\033[1;36m║ Task ID: {task_id.ljust(66)} ║\033[0m")
        print(f"\033[1;36m║ Status: {status_color}{status.ljust(68)}\033[1;36m ║\033[0m")
        print(f"\033[1;36m║ Thread ID: {str(task_info.get('thread_id', 'N/A')).ljust(65)} ║\033[0m")
        print(f"\033[1;36m║ Hater Name: {str(task_info.get('name', 'N/A')).ljust(64)} ║\033[0m")
        print(f"\033[1;36m║ Tokens: {str(len(task_info.get('tokens_all', []))).ljust(68)} ║\033[0m")
        print(f"\033[1;36m║ Messages: {str(task_info.get('msg_count', 'N/A')).ljust(66)} ║\033[0m")
        print(f"\033[1;36m║ Delay: {str(task_info.get('delay', 'N/A')).ljust(70)} ║\033[0m")
        print(f"\033[1;36m║ FB Profile: {str(task_info.get('fb_name', 'Unknown')).ljust(64)} ║\033[0m")
        print(f"\033[1;36m╚{'═' * 78}╝\033[0m")
        print("")

def delete_tasks():
    tasks = load_tasks()
    if not tasks:
        print_status("No tasks found", "warning")
        return
    
    print_section_header("DELETE TASKS")
    
    for i, task_id in enumerate(tasks.keys(), 1):
        print(f"\033[1;36m║ {i}. {task_id}\033[0m")
    
    try:
        choice = int(input("\n\033[1;36m║ Select task to delete (0 to cancel): \033[0m"))
        if choice == 0:
            return
        
        task_ids = list(tasks.keys())
        if 1 <= choice <= len(task_ids):
            task_id = task_ids[choice-1]
            if delete_task(task_id):
                print_status(f"Task {task_id} deleted successfully", "success")
            else:
                print_status("Failed to delete task", "error")
        else:
            print_status("Invalid selection", "error")
    except ValueError:
        print_status("Invalid input", "error")

def main_menu():
    while True:
        clear_screen()
        display_banner()
        
        # Display connection status
        connection_status = "\033[1;32mONLINE\033[0m" if is_connected() else "\033[1;33mOFFLINE\033[0m"
        print(f"\033[1;36m╔{'═' * 40}╗\033[0m")
        print(f"\033[1;36m║ Connection Status: {connection_status.ljust(18)} ║\033[0m")
        print(f"\033[1;36m╚{'═' * 40}╝\033[0m")
        
        print_section_header("MAIN MENU")
        print_menu_option("1", "Start New Task")
        print_menu_option("2", "View Saved Tasks", "\033[1;36m")
        print_menu_option("3", "Delete Tasks", "\033[1;33m")
        print_menu_option("4", "Exit", "\033[1;31m")
        print(f"\033[1;36m╔{'═' * 40}╗\033[0m")
        print(f"\033[1;36m║\033[0m", end="")
        
        choice = input("\033[1;36m Select an option: \033[0m").strip()
        print(f"\033[1;36m╚{'═' * 40}╝\033[0m")
        
        if choice == "1":
            start_new_task()
            input("\nPress Enter to continue...")
        elif choice == "2":
            view_tasks()
            input("\nPress Enter to continue...")
        elif choice == "3":
            delete_tasks()
            input("\nPress Enter to continue...")
        elif choice == "4":
            print_section_header("3XITING 9BHIISH3K L3G3ND T00L. G00DBY3!")
            break
        else:
            print_status("Invalid option", "error")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print_section_header("3XITING 9BHISH3K L3G3ND T00L. G00DBY3!")
        sys.exit(0)