from pathlib import Path


def create_redesign_preview(reference, output, brand, label="BRANDED PREVIEW"):
    from PIL import Image, ImageDraw, ImageFont
    image = Image.open(reference).convert("RGB")
    canvas = Image.new("RGB", image.size, "#" + brand.background_color)
    sidebar = max(42, int(image.width * 0.065))
    target = image.copy(); target.thumbnail((image.width - sidebar - 24, image.height - 40))
    canvas.paste(target, (12, 12))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((image.width - sidebar, 0, image.width, image.height), fill="#" + brand.primary_color)
    draw.rectangle((0, image.height - 26, image.width - sidebar, image.height), fill="#" + brand.accent_color)
    draw.text((18, image.height - 22), label, fill="white", font=ImageFont.load_default())
    canvas.save(output, quality=90)


def create_contact_sheet(paths, output, columns=3, thumb=(480, 270)):
    from PIL import Image, ImageDraw
    paths = list(paths)
    if not paths:
        return None
    rows = (len(paths) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * thumb[0], rows * (thumb[1] + 28)), "white")
    draw = ImageDraw.Draw(canvas)
    for i, path in enumerate(paths):
        im = Image.open(path).convert("RGB"); im.thumbnail(thumb)
        x = (i % columns) * thumb[0]; y = (i // columns) * (thumb[1] + 28)
        canvas.paste(im, (x, y)); draw.text((x + 8, y + thumb[1] + 6), f"Slide {i + 1}", fill="black")
    Path(output).parent.mkdir(parents=True, exist_ok=True); canvas.save(output)
    return output

