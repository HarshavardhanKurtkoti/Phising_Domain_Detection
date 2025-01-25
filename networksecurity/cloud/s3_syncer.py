import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class S3Sync:
    def sync_folder_to_s3(self, folder, aws_bucket_url):
        command = f"aws s3 sync {folder} {aws_bucket_url}"
        logging.info(f"Executing command: {command}")
        os.system(command)
        logging.info(f"Finished syncing {folder} to {aws_bucket_url}")

    def sync_folder_from_s3(self, folder, aws_bucket_url):
        command = f"aws s3 sync {aws_bucket_url} {folder}"
        logging.info(f"Executing command: {command}")
        os.system(command)
        logging.info(f"Finished syncing {aws_bucket_url} to {folder}")
