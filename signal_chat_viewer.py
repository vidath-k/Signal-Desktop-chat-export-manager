#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime

def load_recipients(filename):
    """Load all contacts from the export file"""
    recipients = {}
    with open(filename, 'r') as f:
        for line in f:
            data = json.loads(line)
            if 'recipient' in data and 'contact' in data['recipient']:
                rid = data['recipient']['id']
                contact = data['recipient']['contact']
                name = contact.get('profileGivenName', '')
                if name:
                    recipients[rid] = name
    return recipients

def find_author_name(author_id, recipients, your_id):
    """Map author ID to a display name"""
    if author_id == your_id:
        return "You"
    return recipients.get(author_id, f"Unknown({author_id})")

def load_chats(filename, recipients, your_id):
    """Load all messages and organize by chat"""
    chats = {}
    
    with open(filename, 'r') as f:
        for line in f:
            data = json.loads(line)
            if 'chatItem' in data:
                item = data['chatItem']
                chat_id = item.get('chatId')
                author_id = item.get('authorId')
                timestamp = item.get('dateSent')
                
                # Extract message body
                body = None
                if 'standardMessage' in item and 'text' in item['standardMessage']:
                    body = item['standardMessage']['text'].get('body', '')
                
                if body:
                    if chat_id not in chats:
                        # Get chat name
                        chat_name = recipients.get(chat_id, f"Chat {chat_id}")
                        chats[chat_id] = {
                            'name': chat_name,
                            'messages': []
                        }
                    
                    chats[chat_id]['messages'].append({
                        'timestamp': timestamp,
                        'author_id': author_id,
                        'author_name': find_author_name(author_id, recipients, your_id),
                        'body': body
                    })
    
    return chats

def display_chat_list(chats):
    """Show all available chats with numbers"""
    print("\n" + "="*60)
    print("📱 AVAILABLE CHATS")
    print("="*60)
    
    chat_list = list(chats.items())
    for i, (chat_id, chat_data) in enumerate(chat_list, 1):
        name = chat_data['name']
        msg_count = len(chat_data['messages'])
        print(f"  {i:2}. {name} ({msg_count} messages)")
    
    return chat_list

def save_conversation(messages, chat_name):
    """Save entire conversation to a text file"""
    # Create safe filename
    safe_name = chat_name.replace(' ', '_').replace('/', '_')
    filename = f"chat_with_{safe_name}.txt"
    
    print(f"\n💾 Saving conversation with {chat_name}...")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"CONVERSATION WITH: {chat_name}\n")
        f.write(f"Total Messages: {len(messages)}\n")
        f.write("="*60 + "\n\n")
        
        for i, msg in enumerate(messages, 1):
            # Convert timestamp to readable date
            try:
                dt = datetime.fromtimestamp(int(msg['timestamp']) / 1000)
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = msg['timestamp']
            
            # Write message
            f.write(f"[{time_str}]\n")
            if msg['author_name'] == "You":
                f.write(f"YOU: {msg['body']}\n")
            else:
                f.write(f"{msg['author_name']}: {msg['body']}\n")
            f.write("-"*50 + "\n\n")
    
    # Get file size
    file_size = os.path.getsize(filename)
    if file_size < 1024:
        size_str = f"{file_size} bytes"
    elif file_size < 1024 * 1024:
        size_str = f"{file_size / 1024:.2f} KB"
    else:
        size_str = f"{file_size / (1024 * 1024):.2f} MB"
    
    print(f"✅ Saved: {filename} ({size_str}, {len(messages)} messages)")
    return filename

def main():
    # Check if main.jsonl exists
    jsonl_file = "main.jsonl"
    if not os.path.exists(jsonl_file):
        print(f"❌ Error: {jsonl_file} not found in current directory")
        print("   Make sure you're in the right folder")
        sys.exit(1)
    
    print("📂 Loading Signal chat export...")
    
    # Load data
    recipients = load_recipients(jsonl_file)
    
    # Your ID (from earlier analysis)
    your_id = "6"
    
    # Load all chats
    chats = load_chats(jsonl_file, recipients, your_id)
    
    if not chats:
        print("❌ No conversations found!")
        sys.exit(1)
    
    while True:
        # Display available chats
        chat_list = display_chat_list(chats)
        
        # Get user choice
        print("\n" + "-"*60)
        try:
            choice = input(f"📌 Choose a chat (1-{len(chat_list)}) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("👋 Goodbye!")
                break
            
            idx = int(choice) - 1
            if idx < 0 or idx >= len(chat_list):
                print("❌ Invalid choice, try again")
                continue
            
            chat_id, chat_data = chat_list[idx]
            
            # Save the conversation directly to file
            output_file = save_conversation(chat_data['messages'], chat_data['name'])
            
            print(f"\n📄 You can view the chat with:")
            print(f"   cat {output_file}")
            print(f"   less {output_file}")
            print(f"   nano {output_file}")
            print(f"   or open in any text editor\n")
            
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()
