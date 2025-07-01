# tobor_emoties.py
# Emotie-animaties voor Tobor (MAX7219 LED Matrix)

import time
import random

# === Setup SPI ===
spi = None
SPI_AVAILABLE = False

try:
    import spidev
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000
    SPI_AVAILABLE = True
    print("LED Matrix: SPI hardware initialized successfully")
except Exception as e:
    print(f"LED Matrix: SPI hardware not available: {e}")
    print("LED Matrix: Running in simulation mode")

def write(register, data):
    if SPI_AVAILABLE and spi:
    spi.xfer2([register, data])
    else:
        print(f"LED_MATRIX: Write register {register:02X} = {data:02X}")

def init_display():
    if SPI_AVAILABLE:
    for cmd, data in [
        (0x0F, 0x00),  # display test uit
        (0x0C, 0x01),  # shutdown uit
        (0x0B, 0x07),  # scan limit
        (0x0A, 0x04),  # intensity
        (0x09, 0x00),  # decode mode uit
    ]:
        write(cmd, data)
    else:
        print("LED_MATRIX: Display initialized (simulation mode)")

def show_bitmap(bitmap):
    if SPI_AVAILABLE:
    for i, row in enumerate(bitmap, start=1):
        write(i, row)
    else:
        print("LED_MATRIX: Showing bitmap:")
        for row in bitmap:
            print(f"  {row:08b}")

def clear_display():
    if SPI_AVAILABLE:
    for i in range(1, 9):
        write(i, 0x00)
    else:
        print("LED_MATRIX: Display cleared")

# === Emoties ===

# --- Verliefd ---
def verliefd():
    # Kleine hartvorm (1 seconde)
    small_heart = [
        0b00000000,
        0b00100100,
        0b01111110,
        0b01111110,
        0b00111100,
        0b00011000,
        0b00000000,
        0b00000000
    ]

    # Grote hartvorm (8 rijen)
    big_heart = [
        0b01100110,
        0b11111111,
        0b11111111,
        0b11111111,
        0b01111110,
        0b00111100,
        0b00011000,
        0b00000000
    ]

    # Scrollframes genereren
    def scroll_frames(base_bitmap, steps):
        frames = []
        height = len(base_bitmap)
        for i in range(steps):
            frame = []
            for j in range(8):
                index = (j + i) % height
                frame.append(base_bitmap[index])
            frames.append(frame)
        return frames

    # Animatie starten
    show_bitmap(small_heart)
    time.sleep(1)

    scrolls = scroll_frames(big_heart, 8)
    delay = 9 / len(scrolls)

    start = time.time()
    while time.time() - start < 9:
        for frame in scrolls:
            show_bitmap(frame)
            time.sleep(delay)


# --- Slaperig ---
def slaperig():
    pulses = [
        [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
        [0x00,0x00,0x00,0x10,0x10,0x00,0x00,0x00],
        [0x00,0x00,0x10,0x28,0x28,0x10,0x00,0x00],
        [0x00,0x10,0x28,0x44,0x44,0x28,0x10,0x00]
    ]
    for _ in range(3):
        for frame in pulses + pulses[::-1]:
            show_bitmap(frame)
            time.sleep(random.uniform(0.3, 0.8))
    clear_display()
    time.sleep(0.5)


# --- Genoeg ---
def genoeg():
    adem = [
        [0x18,0x24,0x5A,0x81,0x81,0x5A,0x24,0x18],
        [0x3C,0x42,0xA5,0x81,0x81,0xA5,0x42,0x3C],
        [0x00,0x18,0x24,0x42,0x42,0x24,0x18,0x00]
    ]
    for _ in range(4):
        for frame in adem + adem[::-1]:
            show_bitmap(frame)
            time.sleep(0.3)
    show_bitmap(adem[0])

# --- Verslaving ---
def verslaving():
    path = [(x,y) for y in range(8) for x in (range(8) if y%2==0 else range(7,-1,-1))]
    food = [(2,2),(5,3),(6,5),(3,6)]
    length = 5
    for i in range(64):
        coords = path[max(0,i-length+1):i+1]
        matrix = [[0]*8 for _ in range(8)]
        for (x,y) in coords:
            matrix[y][x] = 1
        if i < len(food)*2:
            fx, fy = food[i % len(food)]
            matrix[fy][fx] = 1
        show_bitmap([sum([val << (7-j) for j,val in enumerate(row)]) for row in matrix])
        time.sleep(0.1)

    # Slang belegering: rondje om het midden
    spiral = [(3,3),(4,3),(5,3),(5,4),(5,5),(4,5),(3,5),(3,4)]
    for _ in range(3):
        for x, y in spiral:
            matrix = [[0]*8 for _ in range(8)]
            matrix[y][x] = 1
            show_bitmap([sum([val << (7-j) for j,val in enumerate(row)]) for row in matrix])
            time.sleep(0.1)

    clear_display()
    time.sleep(0.5)

# --- Boos ---

    
def boos():
    burst = [
        [0x00,0x24,0x5A,0xE7,0xE7,0x5A,0x24,0x00],
        [0x24,0x5A,0xE7,0xFF,0xFF,0xE7,0x5A,0x24],
        [0x5A,0xE7,0xFF,0xFF,0xFF,0xFF,0xE7,0x5A],
        [0xE7,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xE7],
        [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF],
    ]
    for _ in range(3):
        for frame in burst + burst[::-1]:
            show_bitmap(frame)
            time.sleep(0.2)
    show_bitmap([0x00]*8)
    time.sleep(0.5)    

# --- Geïrriteerd ---
def geirriteerd():
    for _ in range(10):
        for r in range(8):
            show_bitmap([1 << (r%8)]*8)
            time.sleep(0.05)
        for i in range(8):
            show_bitmap([1 << i for _ in range(8)])
            time.sleep(0.05)
    show_bitmap([0x00]*8)

# --- Verdrietig ---
def verdrietig():
    def falling_drop(column):
        frames = []
        for y in range(8):
            frame = [0x00] * 8
            if y == 0:
                if 0 <= column <= 7:
                    frame[y] = 1 << (7 - column)
            elif y == 1:
                drop = {
                    0: 0b00000011,
                    1: 0b00000111,
                    2: 0b00001110,
                    3: 0b00011100,
                    4: 0b00111000,
                    5: 0b01110000,
                    6: 0b11100000,
                    7: 0b11000000,
                }
                frame[y] = drop.get(column, 0)
            elif y == 2:
                drop = {
                    0: 0b00000111,
                    1: 0b00001111,
                    2: 0b00011110,
                    3: 0b00111100,
                    4: 0b01111000,
                    5: 0b11110000,
                    6: 0b11100000,
                    7: 0b11000000,
                }
                frame[y] = drop.get(column, 0)
            elif y == 3:
                drop = {
                    0: 0b00000011,
                    1: 0b00000111,
                    2: 0b00001110,
                    3: 0b00011100,
                    4: 0b00111000,
                    5: 0b01110000,
                    6: 0b11100000,
                    7: 0b11000000,
                }
                frame[y] = drop.get(column, 0)
            elif y >= 4:
                if 0 <= column <= 7:
                    frame[y] = 1 << (7 - column)
            frames.append(frame)
        return frames

    init_display()
    columns = [1, 6, 2, 5, 3, 4]
    for col in columns:
        frames = falling_drop(col)
        for frame in frames:
            show_bitmap(frame)
            time.sleep(0.2)
        time.sleep(0.3)
    clear_display()
    time.sleep(2)



# --- Blij ---
def blij():
    circles = [
        [0x00,0x00,0x00,0x18,0x18,0x00,0x00,0x00],
        [0x00,0x00,0x18,0x24,0x24,0x18,0x00,0x00],
        [0x00,0x18,0x24,0x42,0x42,0x24,0x18,0x00],
        [0x18,0x24,0x42,0x81,0x81,0x42,0x24,0x18]
    ]
    spark_patterns = [
        [0x00,0x00,0x08,0x00,0x00,0x08,0x00,0x00],
        [0x00,0x10,0x00,0x00,0x00,0x00,0x10,0x00],
        [0x20,0x00,0x00,0x00,0x00,0x00,0x00,0x20]
    ]
    for _ in range(2):
        for frame in circles:
            show_bitmap(frame)
            time.sleep(0.3)
            show_bitmap(random.choice(spark_patterns))
            time.sleep(0.2)
    for frame in reversed(circles):
        show_bitmap(frame)
        time.sleep(0.4)
    clear_display()
    time.sleep(0.5)

# --- Bang ---
def bang():
    init_display()
    flash = [0xFF, 0x00] * 4
    # Fase 1: snelle flits
    for _ in range(6):
        for row in flash:
            show_bitmap([row]*8)
            time.sleep(0.1)
    # Fase 2: bibberend patroon
    for _ in range(6):
        frame = [random.randint(0x00, 0xFF) for _ in range(8)]
        show_bitmap(frame)
        time.sleep(0.15)
    # Fase 3: trillende kleine kern
    pulse = [
        [0x00,0x00,0x00,0x10,0x10,0x00,0x00,0x00],
        [0x00,0x00,0x10,0x38,0x38,0x10,0x00,0x00],
        [0x00,0x10,0x38,0x7C,0x7C,0x38,0x10,0x00],
        [0x10,0x38,0x7C,0xFE,0xFE,0x7C,0x38,0x10]
    ]
    for _ in range(3):
        for frame in pulse + pulse[::-1]:
            show_bitmap(frame)
            time.sleep(0.1)
    # Fase 4: AI angst - warboel
    for _ in range(8):
        pattern = [random.randint(0, 255) for _ in range(8)]
        show_bitmap(pattern)
        time.sleep(0.2)
    # Fase 5: één pixel blijft branden (paniek verstijft)
    show_bitmap([0x00,0x00,0x00,0x08,0x08,0x00,0x00,0x00])
    time.sleep(1.5)
    clear_display()
    time.sleep(0.5)

# --- Verward ---
def verward():
    ripple_frames = [
        [0b00000000,0b00011000,0b00100100,0b01000010,0b01000010,0b00100100,0b00011000,0b00000000],
        [0b00111100,0b01000010,0b10000001,0b10000001,0b10000001,0b10000001,0b01000010,0b00111100],
        [0b11111111,0b10000001,0b10000001,0b10000001,0b10000001,0b10000001,0b10000001,0b11111111]
    ]

    pulse_sun = [
        0b01000010,0b10100101,0b01111110,0b00111100,0b00111100,0b01111110,0b10100101,0b01000010
    ]

    rotate_frames = [
        [0b00011000,0b00100100,0b01111110,0b10011001,0b10011001,0b01111110,0b00100100,0b00011000],
        [0b00100100,0b01000010,0b10011001,0b01111110,0b01111110,0b10011001,0b01000010,0b00100100],
        [0b01000010,0b10000001,0b00100100,0b11111111,0b11111111,0b00100100,0b10000001,0b01000010],
        [0b10000001,0b01000010,0b00011000,0b01111110,0b01111110,0b00011000,0b01000010,0b10000001]
    ]

    question_mark = [
        0b00111100,0b01000010,0b00000010,0b00001100,0b00010000,0b00000000,0b00010000,0b00000000
    ]

    # Fase 1: Ripple (1.5 sec)
    for frame in ripple_frames:
        show_bitmap(frame)
        time.sleep(0.5)

    # Fase 2: Pulsende zon (1 sec)
    for _ in range(2):
        show_bitmap(pulse_sun)
        time.sleep(0.25)
        clear_display()
        time.sleep(0.25)

    # Fase 3: Rotatie met vraagtekens ertussen
    total_rotate = 12  # seconden
    rotate_per_question = 3  # seconden per blok
    frame_time = 0.125
    frames_per_block = int(rotate_per_question / (len(rotate_frames) * frame_time))

    for _ in range(3):  # 3 blokken van 3 sec
        for _ in range(frames_per_block):
            for frame in rotate_frames:
                show_bitmap(frame)
                time.sleep(frame_time)
        show_bitmap(question_mark)
        time.sleep(0.3)

    # Fase 4: Slotvraagteken (1.5 sec)
    show_bitmap(question_mark)
    time.sleep(1.5)

    # Fase 5: Display uit
    clear_display()


# --- Weigering ---
def weigering():
    patterns = [
        [0xAA,0x55]*4,
        [0x33,0xCC]*4,
        [0x99,0x66]*4,
    ]
    for _ in range(4):
        for pattern in patterns:
            show_bitmap(pattern)
            time.sleep(0.2)
    show_bitmap([0x81,0x42,0x24,0x18,0x18,0x24,0x42,0x81])

# --- Verrast ---
def verrast():
    init_display()
    # Fase 1: willekeurige stippen (chaos)
    for _ in range(10):
        frame = [random.randint(0, 255) for _ in range(8)]
        show_bitmap(frame)
        time.sleep(0.15)

    # Fase 2: symmetrie (balans)
    pattern = [0x18,0x24,0x42,0x81,0x81,0x42,0x24,0x18]
    for _ in range(3):
        show_bitmap(pattern)
        time.sleep(0.3)
        show_bitmap([0x00]*8)
        time.sleep(0.1)

    # Fase 3: pulse (inzicht)
    pulse = [
        [0x00,0x00,0x18,0x3C,0x3C,0x18,0x00,0x00],
        [0x00,0x18,0x3C,0x7E,0x7E,0x3C,0x18,0x00],
        [0x18,0x3C,0x7E,0xFF,0xFF,0x7E,0x3C,0x18]
    ]
    for frame in pulse + pulse[::-1]:
        show_bitmap(frame)
        time.sleep(0.2)

    # Fase 4: collaps naar 1 pixel
    for b in [
        [0x18,0x3C,0x7E,0xFF,0xFF,0x7E,0x3C,0x18],
        [0x00,0x18,0x3C,0x7E,0x7E,0x3C,0x18,0x00],
        [0x00,0x00,0x18,0x3C,0x3C,0x18,0x00,0x00],
        [0x00,0x00,0x00,0x18,0x18,0x00,0x00,0x00],
        [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
    ]:
        show_bitmap(b)
        time.sleep(0.25)

    clear_display()
    time.sleep(0.5)

# --- Octopus ---
def octopus():
    frames = [
        [0x18,0x3C,0x7E,0xDB,0xFF,0x7E,0x24,0x42],
        [0x10,0x38,0x7C,0xDB,0xFF,0x7C,0x28,0x44],
        [0x08,0x1C,0x3E,0xDB,0xFF,0x3E,0x14,0x22],
        [0x10,0x38,0x7C,0xDB,0xFF,0x7C,0x28,0x44],
    ]
    for _ in range(4):
        for frame in frames:
            show_bitmap(frame)
            time.sleep(0.4)
    fade = [
        [b & 0x77 for b in frames[0]],
        [b & 0x33 for b in frames[0]],
        [b & 0x11 for b in frames[0]],
        [0x00]*8
    ]
    for f in fade:
        show_bitmap(f)
        time.sleep(0.3)

# --- Emotie aanroep functie ---
def speel_emotie(naam):
    emoties = {
        "verliefd": verliefd,
        "blij": blij,
        "genoeg": genoeg,
        "verslaving": verslaving,
        "boos": boos,
        "geirriteerd": geirriteerd,
        "verdrietig": verdrietig,
        "slaperig": slaperig,
        "bang": bang,
        "verward": verward,
        "weigering": weigering,
        "verrast": verrast,
        "octopus": octopus,
    }
    if naam in emoties:
        emoties[naam]()
    else:
        print(f"Onbekende emotie: {naam}")

# Optioneel: initialiseer display bij starten
init_display() 