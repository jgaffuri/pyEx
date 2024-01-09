# python3 -m venv venv
# source venv/bin/activate
# pip install Pillow
# python -m PIL
# deactivate

from PIL import Image, ImageSequence, Image

def create_gif(input_path, input_images, output_gif_path, gif_size=(300, 300), duration=200, loop=0, optimize=True):
    """
    Create a GIF animation from a list of input images.

    Parameters:
    - input_images: List of input image file paths.
    - output_gif_path: Output GIF file path.
    - gif_size: Tuple specifying the size of the output GIF (width, height).
    - duration: Duration (in milliseconds) for each frame in the GIF.

    Returns:
    None
    """
    frames = []

    for image_path in input_images:
        image = Image.open(input_path + image_path)

        # Resize the image to the specified GIF size
        image = image.resize(gif_size, resample=Image.LANCZOS)

        # Convert RGBA images to RGB
        if image.mode == 'RGBA':
            image = image.convert('RGB')

        #
        #image = image.convert('P', palette=Image.ADAPTIVE, colors=256)

        frames.append(image)

    # Save the frames as a GIF
    frames[0].save(
        output_gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=loop,  # 0 means an infinite loop
        optimize=optimize  # compression
    )

# Example usage:
input_path = "/home/juju/orienteering/omap_thionville_fameck/exports/"
input_images = [f"{i}.png" for i in range(2, 22)]
output_gif_path = "/home/juju/Bureau/output.gif"
create_gif(input_path, input_images, output_gif_path, gif_size=(992, 702), duration=800)
