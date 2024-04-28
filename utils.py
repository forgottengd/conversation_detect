import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import numpy as np
from typing import List, Tuple
from io import BytesIO


def process_rectangle(coords: List) -> Tuple:
    x = int(coords[0]['x'])
    y = int(coords[0]['y'])
    width = int(coords[2]['x']) - x
    height = int(coords[2]['y']) - y
    return x, y, width, height


def draw_rectangles(image_path, blocks, sentences):
    """
    Отображает прямоугольники на изображении.

    :param sentences: список найденных предложений с прямоугольниками (x1, x2, y1, y2)
    :param image_path: путь к файлу изображения.
    :param blocks: список прямоугольников, где каждый прямоугольник задается как (x, y, width, height).
    """
    # Загрузка изображения
    img = Image.open(image_path)
    img_np = np.array(img)

    dpi = 300  # Разрешение в точках на дюйм, можно адаптировать
    height, width, _ = img_np.shape
    figsize = width / float(dpi), height / float(dpi)  # Размер фигуры в дюймах
    # Создание фигуры и осей
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.imshow(img_np)

    # Добавление прямоугольников OCR
    rectangles = []
    for block in blocks:
        rectangles.append(process_rectangle(block['boundingBox']['vertices']))
    for (x, y, width, height) in rectangles:
        rect = patches.Rectangle((x, y), width, height, linewidth=0.9, edgecolor='r', facecolor='none')
        ax.add_patch(rect)

    # Добавление прямоугольников Processed_OCR
    for sent in sentences:
        rect = patches.Rectangle((sent["x1"], sent["y1"]), sent["x2"] - sent["x1"], sent["y2"] - sent["y1"],
                                 linewidth=1, edgecolor='g', facecolor='none')
        ax.add_patch(rect)

    # Убираем оси и белые поля
    ax.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # Сохраняем фигуру в объект BytesIO для последующего использования в Streamlit
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    # Возвращаем объект BytesIO, который можно отобразить в Streamlit
    return buf
