import pandas as pd

import os
import subprocess
import shutil
from pathlib import Path
import logging
from dotenv import load_dotenv

import boto3
from botocore.exceptions import ClientError

load_dotenv() 

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="migration_log.log",
    filemode="a"
)

wc_csv = Path(os.getenv("WC_CSV")) #TODO fix esc char
products_parent = Path(os.getenv("PRODUCTS_PARENT")) #TODO fix esc char
extensions = os.getenv("EXTENSIONS", "jpg,jpeg,png").split(",")

bucket = os.getenv("BUCKET_NAME")
access_key_id=os.getenv('ACCESS_KEY_ID')
secret_access_key=os.getenv("SECRET_ACCESS_KEY")

def process_csv(wc_csv):
    wc_photo_df = pd.read_csv(wc_csv)
    # filter so only photos for products that are published (not drafts or in the trash) will be downloaded
    wc_photos_filtered = wc_photo_df[
        (wc_photo_df['published'] == 1) &
        (~wc_photo_df['Images'].str.match(r'^\s*$', na=True)) # also exclude products with no photos
    ]

    return wc_photos_filtered

def download_photos(wc_photos_filtered, products_parent):
    for index, row in wc_photos_filtered.iterrows():
        product_name = row['Name'].strip()
        photo_urls = [url.strip() for url in row['Images'].split(',')]

        product_folder = products_parent / product_name
        product_folder.mkdir(exist_ok=True)

        for url in photo_urls:
            parsed_url = urlparse(url)
            img_file_name = Path(parsed_url.path).name # name the image file according to the last part of the URL
            image = product_folder / img_file_name # where the image will be saved
            if not image.exists():
                result = subprocess.run(['wget', url, '-O', str(image)], capture_output=True)
                if result.returncode == 0 and os.path.getsize(image) > 0:
                    # TODO log to file (f"Successfully downloaded {url} to {image}")
                    print(f"Successfully downloaded {url} to {image}") #TODO fix logging
                else:
                    # TODO log to file f"Failed to download {url}: {result.stderr.decode().strip()}")
                    if image.exists():
                        os.remove(image) # delete file if it's there and empty/corrupted

    print("Done downloading all the product photos")
    
    products_parent = Path(products_parent)
    backup_folder = products_parent.parent / (products_parent.name + "_backup")

    if backup_folder.exists():
        print(f"Backup folder {backup_folder} already exists. Skipping copy step.")
    else:
        print("Making a copy of the photo folder as a backup...")
        shutil.copytree(products_parent, backup_folder)
        print(f"Backup of original photos created at {backup_folder}")

def convert_to_webp(products_parent: Path, extensions: set = {".jpg", ".jpeg", ".png"}, quality: int = 90) -> None:
    products_parent = Path(products_parent)
    if not products_parent.exists() or not products_parent.is_dir():
        log.error(f"Error: no product parent directory found")
        return

    for product_folder in products_parent.iterdir():
        if not product_folder.is_dir():
            continue
            
        for image in product_folder.iterdir():
            if image.suffix.lower() not in extensions:
                continue
            webp_version = image.with_suffix(".webp")
            try:
                with Image.open(image) as img:
                    img.save(webp_version, "WEBP", quality=quality)
                    log.info(f"Converted {image} to {webp_version}")
            except Exception as exc:
                log.error(f"Error: could not convert {image}: {exc}")

    log.info("WebP conversion finished")

def upload_to_s3(products_parent, bucket):
    """
    Upload all the *.webp product photos to the S3 bucket.
    Uses the product name as a metadata tag `x-amz-meta-product`.
    """
    s3 = boto3.client(
    "s3",
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key
    )
    products_parent = Path(products_parent)

    for product_folder in products_parent.iterdir():
        s3_prefix = product_folder.name
        for image in product_folder.glob("*.webp"):
            object_key = image.relative_to(products_parent).as_posix()
            try:
                s3.upload_file(
                    image,
                    bucket,
                    object_key,
                    ExtraArgs={
                            "ContentType": "image/webp",
                            "Metadata": {"product": product_folder.name},
                            "ACL": "public-read"
                    },
                    )
                #log.info("Uploaded %s to s3://%s/%s", image.name, bucket, object_key)
            except ClientError as exception:
                print("Failed to upload %s: %s", image, exception)
               # log.error("Failed to upload %s: %s", image, exception)

    log.info("S3 upload finished.")

df = process_csv(wc_csv)
download_photos(df, products_parent)
convert_to_webp(products_parent, extensions)
upload_to_s3(products_parent, bucket)

