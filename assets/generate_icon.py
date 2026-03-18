"""
Generare icon .ico pentru Calculator Pret Traduceri.
Creeaza un icon profesional 256x256 + 48x48 + 32x32 + 16x16
cu design calculator + RON, fara dependente externe.
"""

import struct
import zlib
import os

def create_png_icon(size):
    """Creeaza un icon PNG in memorie — calculator cu simbol RON."""
    pixels = []

    # Culori
    BG_DARK = (15, 23, 42)        # slate-900
    BG_MID = (30, 41, 59)         # slate-800
    PRIMARY = (59, 130, 246)      # blue-500
    PRIMARY_LIGHT = (96, 165, 250) # blue-400
    ACCENT = (16, 185, 129)       # emerald-500
    WHITE = (255, 255, 255)
    GOLD = (251, 191, 36)         # amber-400

    cx, cy = size / 2, size / 2
    r_outer = size * 0.45
    r_inner = size * 0.38

    for y in range(size):
        row = []
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = (dx*dx + dy*dy) ** 0.5

            # Fundal transparent in afara cercului
            if dist > r_outer + 1:
                row.append((0, 0, 0, 0))
                continue

            # Anti-aliasing pe margine
            if dist > r_outer:
                alpha = max(0, min(255, int(255 * (r_outer + 1 - dist))))
                row.append((*PRIMARY, alpha))
                continue

            # Cerc exterior — gradient albastru
            if dist > r_inner:
                t = (dist - r_inner) / (r_outer - r_inner)
                r = int(PRIMARY[0] * (1-t) + PRIMARY_LIGHT[0] * t)
                g = int(PRIMARY[1] * (1-t) + PRIMARY_LIGHT[1] * t)
                b = int(PRIMARY[2] * (1-t) + PRIMARY_LIGHT[2] * t)
                row.append((r, g, b, 255))
                continue

            # Interior — fundal dark
            # Normalizam pozitia relativa la interior
            nx = (x - cx) / r_inner  # -1 to 1
            ny = (y - cy) / r_inner  # -1 to 1

            # Desenam "RON" stilizat sau un simbol de calculator
            pixel = (*BG_DARK, 255)

            # Grid de calculator (linii subtiri)
            grid_size = r_inner * 0.18
            gx = ((x - cx + r_inner) % grid_size) / grid_size
            gy = ((y - cy + r_inner) % grid_size) / grid_size

            # Zona de display (sus)
            if -0.8 < nx < 0.8 and -0.75 < ny < -0.3:
                pixel = (*BG_MID, 255)

                # "LEI" text area — bara subtire green
                if -0.7 < nx < 0.7 and -0.65 < ny < -0.45:
                    # Gradient verde
                    t = (nx + 0.7) / 1.4
                    r = int(ACCENT[0] * 0.7 + PRIMARY[0] * 0.3 * t)
                    g = int(ACCENT[1] * 0.7 + PRIMARY[1] * 0.3 * t)
                    b = int(ACCENT[2] * 0.7 + PRIMARY[2] * 0.3 * t)
                    pixel = (r, g, b, 255)

            # Zona de butoane (jos) — grid 3x3
            elif -0.7 < nx < 0.7 and -0.15 < ny < 0.75:
                col = int((nx + 0.7) / 1.4 * 3)
                row_idx = int((ny + 0.15) / 0.9 * 3)

                # Celula buton
                cell_nx = ((nx + 0.7) / 1.4 * 3) % 1
                cell_ny = ((ny + 0.15) / 0.9 * 3) % 1

                # Margini celula
                if 0.08 < cell_nx < 0.92 and 0.08 < cell_ny < 0.92:
                    if col == 2 and row_idx == 2:
                        # Buton special (=) — gold
                        pixel = (*GOLD, 255)
                    elif col == 2:
                        # Coloana operatii — primary light
                        pixel = (*PRIMARY_LIGHT, 255)
                    else:
                        # Butoane numerice — slate
                        pixel = (51, 65, 85, 255)  # slate-700

            # Simbol RON — mic cerc in coltul din dreapta-sus
            ron_cx = cx + r_inner * 0.55
            ron_cy = cy - r_inner * 0.55
            ron_dist = ((x - ron_cx)**2 + (y - ron_cy)**2) ** 0.5
            ron_r = r_inner * 0.22
            if ron_dist < ron_r:
                pixel = (*GOLD, 255)
            elif ron_dist < ron_r + 1:
                alpha = max(0, min(255, int(255 * (ron_r + 1 - ron_dist))))
                pixel = (*GOLD, alpha)

            row.append(pixel)
        pixels.append(row)

    return _encode_png(pixels, size, size)


def _encode_png(pixels, width, height):
    """Encode pixel data as PNG."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack('>I', len(data)) + c + crc

    # PNG signature
    sig = b'\x89PNG\r\n\x1a\n'

    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    ihdr = chunk(b'IHDR', ihdr_data)

    # IDAT
    raw_data = b''
    for row in pixels:
        raw_data += b'\x00'  # filter: none
        for r, g, b, a in row:
            raw_data += struct.pack('BBBB', r, g, b, a)

    compressed = zlib.compress(raw_data, 9)
    idat = chunk(b'IDAT', compressed)

    # IEND
    iend = chunk(b'IEND', b'')

    return sig + ihdr + idat + iend


def create_ico(output_path):
    """Creeaza fisier .ico cu mai multe dimensiuni."""
    sizes = [256, 48, 32, 16]
    images = []

    for size in sizes:
        print(f"  Generare {size}x{size}...")
        png_data = create_png_icon(size)
        images.append((size, png_data))

    # ICO header
    ico_header = struct.pack('<HHH', 0, 1, len(images))

    # Calculate offsets
    dir_entry_size = 16
    offset = 6 + dir_entry_size * len(images)

    directory = b''
    image_data = b''

    for size, png_data in images:
        w = 0 if size == 256 else size  # 0 means 256
        h = 0 if size == 256 else size

        directory += struct.pack(
            '<BBBBHHII',
            w, h,       # width, height (0 = 256)
            0,          # color palette
            0,          # reserved
            1,          # color planes
            32,         # bits per pixel
            len(png_data),  # size
            offset,     # offset
        )

        image_data += png_data
        offset += len(png_data)

    with open(output_path, 'wb') as f:
        f.write(ico_header + directory + image_data)

    print(f"  Icon salvat: {output_path} ({os.path.getsize(output_path)} bytes)")


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(script_dir, 'calculator_icon.ico')

    print("=" * 50)
    print("  Generare Icon — Calculator Pret Traduceri")
    print("=" * 50)
    create_ico(ico_path)
    print("  Done!")
