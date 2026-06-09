import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from telethon import TelegramClient, events
from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument, 
    PeerUser, PeerChat, PeerChannel, User, Chat, Channel
)


class ConfigModel:
    def __init__(self, data=None):
        if data is None:
            data = {}
        self.enable_wtelegram_logs = data.get("EnableWTelegramLogs", False)
        self.api_id = data.get("ApiId", 0)
        self.api_hash = data.get("ApiHash", "")
        self.phone_number = data.get("PhoneNumber", "")
        self.forward_to_saved_messages = data.get("ForwardToSavedMessages", True)
        self.max_file_size_mb = data.get("MaxFileSizeMB", 250)
        self.include_chat_title_in_caption = data.get("IncludeChatTitleInCaption", True)
        self.auto_create_config = data.get("AutoCreateConfig", True)


class TelegramSelfDestructDownloader:
    def __init__(self):
        self.config_file = "appsettings.json"
        self.log_folder = "Logs"
        self.session_folder = "sessions"
        self.users = {}
        self.chats = {}
        self.client = None
        self.config = None
        
        # Create necessary directories
        Path(self.log_folder).mkdir(exist_ok=True)
        Path(self.session_folder).mkdir(exist_ok=True)

    def log(self, text):
        """Write to log file"""
        try:
            timestamp = datetime.utcnow().isoformat()
            line = f"[{timestamp}] {text}\n"
            log_path = os.path.join(self.log_folder, "log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            print(f"Error writing to log: {e}")

    def info(self, text):
        """Print and log info"""
        print(text)
        self.log(text)

    def load_or_create_config(self):
        """Load config from file or create new one"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                config = ConfigModel(data)
                if config.api_id != 0 and config.api_hash and config.phone_number:
                    return config
                print("Config file is incomplete. You will be guided to create it.")
            except Exception as e:
                print(f"Failed to read config file: {e}")

        print("Create a new configuration (appsettings.json). This is needed only once.")
        if not self.prompt_yes_no("Create config now? (Y/n)"):
            return None

        config = ConfigModel()
        
        # Get API ID
        while True:
            try:
                api_id_str = input("ApiId (digits): ").strip()
                api_id = int(api_id_str)
                if api_id > 0:
                    config.api_id = api_id
                    break
                print("Please enter a valid numeric ApiId.")
            except ValueError:
                print("Please enter a valid numeric ApiId.")

        config.api_hash = input("ApiHash: ").strip() or ""
        config.phone_number = input("Phone number (with +): ").strip() or ""

        print(f"Saving config to {self.config_file}")
        config_dict = {
            "EnableWTelegramLogs": config.enable_wtelegram_logs,
            "ApiId": config.api_id,
            "ApiHash": config.api_hash,
            "PhoneNumber": config.phone_number,
            "ForwardToSavedMessages": config.forward_to_saved_messages,
            "MaxFileSizeMB": config.max_file_size_mb,
            "IncludeChatTitleInCaption": config.include_chat_title_in_caption,
            "AutoCreateConfig": config.auto_create_config,
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        self.log("Configuration file created.")
        return config

    @staticmethod
    def prompt_yes_no(question):
        """Prompt user for yes/no answer"""
        answer = input(question + " ").strip().lower()
        if not answer:
            return True
        return answer in ("y", "yes")

    @staticmethod
    def get_session_path(phone_number):
        """Get session file path"""
        safe_phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")
        return os.path.join("sessions", f"session_{safe_phone}")

    @staticmethod
    def make_safe_filename(name):
        """Make filename safe for Windows/Unix"""
        invalid_chars = r'[<>:"/\\|?*]'
        return re.sub(invalid_chars, "_", name)

    @staticmethod
    def get_chat_title(message, users, chats):
        """Get chat title from message peer"""
        try:
            if isinstance(message.peer_id, PeerUser):
                user = users.get(message.peer_id.user_id)
                if user:
                    return user.username or f"{user.first_name} {user.last_name}".strip()
            elif isinstance(message.peer_id, PeerChat):
                chat = chats.get(message.peer_id.chat_id)
                if chat and hasattr(chat, 'title'):
                    return chat.title or "Group"
            elif isinstance(message.peer_id, PeerChannel):
                channel = chats.get(message.peer_id.channel_id)
                if channel and hasattr(channel, 'title'):
                    return channel.title or "Channel"
        except:
            pass
        return "Unknown chat"

    async def handle_message(self, message):
        """Handle incoming message"""
        try:
            if message is None:
                return

            # Skip outgoing messages
            if message.out:
                return

            media = None
            file_name = None
            ttl = None

            chat_title = self.get_chat_title(message, self.users, self.chats)

            # Check for view-once photo
            if isinstance(message.media, MessageMediaPhoto):
                if message.media.ttl_seconds and message.media.ttl_seconds > 0:
                    media = message.media.photo
                    ttl = message.media.ttl_seconds
                    file_name = f"viewonce_photo_{message.id}.jpg"

            # Check for view-once document
            elif isinstance(message.media, MessageMediaDocument):
                if message.media.ttl_seconds and message.media.ttl_seconds > 0:
                    media = message.media.document
                    ttl = message.media.ttl_seconds
                    file_name = message.media.document.attributes[0].file_name if message.media.document.attributes else f"viewonce_media_{message.id}"

            if media is None or ttl is None:
                return

            safe_name = self.make_safe_filename(file_name or f"media_{message.id}")

            self.log(f"Detected view-once media ({ttl}s) from {chat_title}: {safe_name}")
            print(f"Detected view-once media from {chat_title}")

            temp_file = None
            try:
                # Download file to temp location
                temp_file = await self.client.download_media(media, file=None)
                
                if temp_file is None:
                    self.log(f"Failed to download media {safe_name} from {chat_title}")
                    return

                file_size = os.path.getsize(temp_file)
                max_size_bytes = self.config.max_file_size_mb * 1024 * 1024

                if file_size > max_size_bytes:
                    self.log(f"Skipping file {safe_name} from {chat_title}: size {file_size} bytes exceeds limit {self.config.max_file_size_mb} MB")
                    print(f"Skipping large file from {chat_title}")
                    return

                # Upload file
                uploaded_file = await self.client.upload_file(temp_file)

                if self.config.forward_to_saved_messages:
                    caption = f"From: {chat_title}" if self.config.include_chat_title_in_caption else ""
                    await self.client.send_file("me", uploaded_file, caption=caption)
                    self.log(f"Forwarded {safe_name} to Saved Messages (from {chat_title})")
                    print(f"Forwarded view-once media {safe_name} from {chat_title}")

            except Exception as e:
                self.log(f"Error processing message {message.id}: {e}")
                print(f"Error processing message from {chat_title}: {e}")
            finally:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass

        except Exception as e:
            self.log(f"Error in handle_message: {e}")

    async def main(self):
        """Main function"""
        self.info("Starting TelegramSelfDestructDownloader...")

        self.config = self.load_or_create_config()
        if self.config is None:
            print("Configuration was not created. Exiting.")
            return

        try:
            session_path = self.get_session_path(self.config.phone_number)
            
            # Create client
            self.client = TelegramClient(
                session_path,
                self.config.api_id,
                self.config.api_hash
            )

            # Setup logging if enabled
            if self.config.enable_wtelegram_logs:
                import logging
                logging.basicConfig(level=logging.DEBUG)

            await self.client.start(phone=self.config.phone_number)
            me = await self.client.get_me()
            
            username = me.username or f"{me.first_name} {me.last_name}".strip()
            print(f"Logged in as: {username}")
            self.log(f"Logged in as: {me.id} / {me.username}")

            # Set up message handler
            @self.client.on(events.NewMessage)
            async def on_new_message(event):
                message = event.message
                
                # Collect user and chat info
                if message.sender_id and isinstance(message.sender_id, int):
                    try:
                        sender = await self.client.get_entity(message.sender_id)
                        if isinstance(sender, User):
                            self.users[message.sender_id] = sender
                    except:
                        pass

                if message.peer_id:
                    try:
                        chat = await self.client.get_entity(message.peer_id)
                        if isinstance(message.peer_id, PeerUser):
                            if isinstance(chat, User):
                                self.users[message.peer_id.user_id] = chat
                        elif isinstance(message.peer_id, PeerChat):
                            if isinstance(chat, Chat):
                                self.chats[message.peer_id.chat_id] = chat
                        elif isinstance(message.peer_id, PeerChannel):
                            if isinstance(chat, Channel):
                                self.chats[message.peer_id.channel_id] = chat
                    except:
                        pass

                await self.handle_message(message)

            print("Listening for incoming messages. Press Ctrl+C to exit.")
            await self.client.run_until_disconnected()

        except KeyboardInterrupt:
            print("Shutting down...")
        except Exception as e:
            self.log(f"Fatal error in Main: {e}")
            print("Fatal error. See Logs/log.txt for details.")
        finally:
            if self.client:
                await self.client.disconnect()


async def main():
    downloader = TelegramSelfDestructDownloader()
    await downloader.main()


if __name__ == "__main__":
    asyncio.run(main())
