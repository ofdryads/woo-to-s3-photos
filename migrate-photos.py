import os
import logging
from pathlib import Path
import pandas as pd
import boto3
from botocore.exceptions import ClientError
from PIL import Image
import requests
from dotenv import load_dotenv
import shutil

load_dotenv() 

# setup log that will log which photos succeed, which have any issues
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="migration_log.log",
    filemode="a"
)
logger = logging.getLogger(__name__)

WC_CSV = Path(os.getenv("WC_CSV"))
PRODUCTS_PARENT = Path(os.getenv("PRODUCTS_PARENT"))
EXTENSIONS = {f".{ext.lower()}" for ext in os.getenv("EXTENSIONS", "jpg,jpeg,png").split(",")} #fallback on common

BUCKET = os.getenv("BUCKET_NAME")
ACCESS_KEY_ID = os.getenv("ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")
ACL_POLICY = os.getenv("ACL_POLICY")

# filter so only photos for products that are published (not drafts or in the trash) will be downloaded
def process_csv(csv_path: Path) -> pd.DataFrame:
    wc_photo_df = pd.read_csv(csv_path)
    wc_photos_filtered = wc_photo_df[
        (wc_photo_df["Published"] == 1) &
        (wc_photo_df["Images"].notna()) & # also exclude products with no photos
        (wc_photo_df["Images"].str.strip() != "")
    ]
    logger.info("%d published products with images", len(wc_photos_filtered))
    return wc_photos_filtered

def sanitize_name(name: str) -> str:
    illegal = '\\/:*?"<>|'
    for char in illegal:
        name = name.replace(char, "_")
    return name.strip()

def download_photos(wc_photos_filtered: pd.DataFrame, products_parent: Path) -> None:
    for _, row in wc_photos_filtered.iterrows():
        product_name = sanitize_name(row['Name'])
        photo_urls = [url.strip() for url in row['Images'].split(',')]

        product_folder = products_parent / product_name
        product_folder.mkdir(exist_ok=True)

        for url in photo_urls:
            img_file = url.split('/')[-1] # name the file by only the last part of the URL
            image = product_folder / img_file # where the image will be saved

            if image.exists():
                continue
            
            try:
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                with open(image, "wb") as f:
                    f.write(response.content)
                if image.stat().st_size == 0: # bad file
                    image.unlink()
                    logger.warning("Downloaded empty file from %s - deleted the bad file", url)
                else:
                    logger.info("Downloaded %s -> %s", url, image)
            except Exception as exc:
                logger.error("Download failed for %s: %s", url, exc)

    print("Done downloading the product photos.")
    
def backup_originals(products_parent: Path):
    backup_folder = products_parent.parent / (products_parent.name + "_backup")
    if not backup_folder.exists():
        shutil.copytree(products_parent, backup_folder)
        logger.info("Created backup of original photos at %s", backup_folder)
    else:
        print(f"Backup folder {backup_folder} already exists. Skipping copy step.")

# compromise between size and img quality
def convert_to_webp(products_parent: Path, extensions: set, quality: int = 90) -> None:
    for product_folder in products_parent.iterdir():
        if not product_folder.is_dir():
            continue
            
        for image in product_folder.iterdir():
            if image.suffix.lower() not in extensions:
                continue
            webp_version = image.with_suffix(".webp")
            if webp_version.exists():
                continue
            try:
                with Image.open(image) as img:
                    img.save(webp_version, "WEBP", quality=quality)
                logger.info(f"Converted {image} to {webp_version}")
            except Exception as exc:
                logger.error(f"Error: could not convert {image}: {exc}")

    logger.info("WebP conversion finished")

def upload_to_s3(products_parent: Path, bucket: str) -> None:
    """
    Upload all the *.webp product photos to the S3 bucket.
    Uses the product name as a metadata tag `x-amz-meta-product`.
    """
    s3 = boto3.client(
        "s3",
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=SECRET_ACCESS_KEY,
    )

    for product_folder in products_parent.iterdir():
        for image in product_folder.glob("*.webp"):
            object_key = image.relative_to(products_parent).as_posix()
            try:
                s3.upload_file(
                    str(image),
                    bucket,
                    object_key,
                    ExtraArgs={
                            "ContentType": "image/webp",
                            "Metadata": {"product": product_folder.name},
                            "ACL": ACL_POLICY
                    },
                )
                logger.info("Uploaded %s to s3://%s/%s", image.name, bucket, object_key)
            except ClientError as exception:
                logger.error("Failed to upload %s: %s", image, exception)

    logger.info("S3 upload finished.")

def main():
    if not WC_CSV.exists():
        raise FileNotFoundError(f"Product info CSV not found at {WC_CSV}")
    if not PRODUCTS_PARENT.exists():
        PRODUCTS_PARENT.mkdir(parents=True)

    wc_df = process_csv(WC_CSV)
    download_photos(wc_df, PRODUCTS_PARENT)
    backup_originals(PRODUCTS_PARENT)
    convert_to_webp(PRODUCTS_PARENT, EXTENSIONS)
    upload_to_s3(PRODUCTS_PARENT, BUCKET)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Photo migration did not work: %s", e)

