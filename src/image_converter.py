import concurrent.futures
import io
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import pillow_heif
import streamlit as st
from loguru import logger
from PIL import Image

@dataclass
class ProcessedImage:
    original_name: str
    image: Image.Image


class ImageProcessor:
    @staticmethod
    def process_heic(file) -> Image.Image:
        logger.debug(f"Processing HEIC file: {file.name}")
        heif_file = pillow_heif.read_heif(file)
        return Image.frombytes(
            heif_file.mode,
            heif_file.size,
            heif_file.data,
            "raw",
            heif_file.mode,
            heif_file.stride,
        )

    @staticmethod
    def process_image(file) -> ProcessedImage:
        logger.info(f"Processing image: {file.name}")
        try:
            if file.name.lower().endswith(".heic"):
                image = ImageProcessor.process_heic(file)
            else:
                image = Image.open(file)
            logger.success(f"Successfully processed: {file.name}")
            return ProcessedImage(file.name, image)
        except Exception as e:
            logger.error(f"Error processing {file.name}: {str(e)}")
            raise

    @staticmethod
    def process_images_parallel(files) -> List[ProcessedImage]:
        logger.info(f"Starting parallel processing of {len(files)} images")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            return list(executor.map(ImageProcessor.process_image, files))


class ImageConverter:
    @staticmethod
    def convert_to_buffer(
        processed_image: ProcessedImage, target_format: str
    ) -> Tuple[str, bytes]:
        img_buffer = io.BytesIO()
        processed_image.image.save(img_buffer, format=target_format)
        base_name = Path(processed_image.original_name).stem
        new_name = f"{base_name}.{target_format.lower()}"
        return new_name, img_buffer.getvalue()

    @staticmethod
    def create_zip(processed_images: List[ProcessedImage], target_format: str) -> bytes:
        logger.info(
            f"Creating ZIP with {len(processed_images)} images in {target_format} format"
        )
        zip_buffer = io.BytesIO()
        from zipfile import ZipFile

        with ZipFile(zip_buffer, "w") as zip_file:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        ImageConverter.convert_to_buffer, img, target_format
                    )
                    for img in processed_images
                ]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        new_name, image_data = future.result()
                        zip_file.writestr(new_name, image_data)
                        logger.debug(f"Added {new_name} to ZIP")
                    except Exception as e:
                        logger.error(f"Error adding file to ZIP: {str(e)}")

        logger.success("ZIP file created successfully")
        return zip_buffer.getvalue()


def render_image_converter():
    logger.info("Rendering image converter page")
    st.title("Image Converter")

    # Initialize session state
    if "processed_images" not in st.session_state:
        logger.debug("Initializing session state")
        st.session_state.processed_images = None
        st.session_state.last_files_processed = None
        st.session_state.last_format = None
        st.session_state.zip_cache = {}

    uploaded_files = st.file_uploader(
        "Choose image files",
        type=["png", "jpg", "jpeg", "webp", "heic"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        target_format = st.selectbox("Convert to:", ["PNG", "JPEG", "WebP"])

        # Check if we need to reprocess the images
        needs_processing = (
            st.session_state.processed_images is None
            or st.session_state.last_files_processed is None
            or len(uploaded_files) != len(st.session_state.last_files_processed)
            or any(
                f1.name != f2.name
                for f1, f2 in zip(uploaded_files, st.session_state.last_files_processed)
            )
            or target_format != st.session_state.last_format
        )

        if needs_processing:
            # Reset state when files or format change
            st.session_state.processed_images = None
            st.session_state.zip_cache = {}

            logger.info("Files or format changed, showing conversion button")
            st.info(
                f"Ready to convert **{len(uploaded_files)}** images to: **{target_format}**"
            )
            if st.button("Convert All", type="primary", use_container_width=True):
                logger.info(f"Starting conversion process to {target_format}")
                with st.spinner("Processing images..."):
                    st.session_state.processed_images = (
                        ImageProcessor.process_images_parallel(uploaded_files)
                    )
                    st.session_state.last_files_processed = uploaded_files
                    st.session_state.last_format = target_format

                logger.success("Conversion process completed")
                st.rerun()

        # Only show results if processing is complete
        if st.session_state.processed_images is not None:
            st.success(
                f"**{len(uploaded_files)}** images processed and ready for download!"
            )

            if st.toggle("Show processed images"):
                logger.debug("Displaying image gallery")
                st.subheader("Processed Images")
                cols = st.columns(3)
                for idx, proc_image in enumerate(st.session_state.processed_images):
                    with cols[idx % 3]:
                        st.image(
                            proc_image.image,
                            caption=proc_image.original_name,
                            use_container_width=True,
                        )

            # Create ZIP only if needed
            if target_format not in st.session_state.zip_cache:
                logger.info(f"Creating ZIP for format: {target_format}")
                with st.spinner("Creating ZIP file..."):
                    zip_data = ImageConverter.create_zip(
                        st.session_state.processed_images, target_format
                    )
                    st.session_state.zip_cache[target_format] = zip_data
            else:
                logger.info(f"Using cached ZIP for format: {target_format}")
                zip_data = st.session_state.zip_cache[target_format]

            st.download_button(
                label="Download All Converted Images",
                data=zip_data,
                file_name=f"converted_images_{target_format.lower()}.zip",
                mime="application/zip",
                use_container_width=True,
            )
