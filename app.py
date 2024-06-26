import streamlit as st
import time
from src.image_processing import process_image, plot_results
from src.tesseract import process_image_tesseract, parse_ocr_tesseract, parse_image_tesseract
from src.utils import draw_rectangles_yandex, elapsed_time, draw_rectangles_tesseract, encode_file_to_base64, \
    get_color_zones
from src.yandex import send_ocr_request_yandex, process_ocr_yandex, process_dict_yandex


block_percentile = 0.18  # зона в которую должен входить блок, чтобы считать его за переписку


def on_upload_yandex(file, temp, folder_id, api_key):
    """ Вызывает обработку загруженного изображения и отображает результат """
    with st.spinner("Detecting image..."):
        try:
            start_time = time.time()  # засекаем время
            image = encode_file_to_base64(file.getvalue())
            ocr_response = send_ocr_request_yandex(api_key, image, folder_id)
            elapsed1 = elapsed_time(start_time, time.time())
            print(f"send_ocr_request_yandex обработан за {elapsed1}")
            # parse OCR result
            if 'error' in ocr_response:
                raise Exception(ocr_response['error'])
            full_text, result_dict = process_ocr_yandex(ocr_response, block_percentile)
            print(f"process_ocr_yandex обработан за {elapsed_time(start_time, time.time())}")
            start2 = time.time()
            image_with_zones_found, bounding_boxes = get_color_zones(file, ocr_response, block_percentile)
            elapsed2 = elapsed_time(start2, time.time())
            print(f"get_color_zones обработан за {elapsed_time(start_time, time.time())}")
            confidence = process_dict_yandex(result_dict, bounding_boxes)
            decision = "Переписка" if confidence >= temp else "Не переписка"
            decision += (f". Уверенность: {confidence} при уровне {temp}. "
                         f"Время выполнения: {elapsed_time(start_time, time.time())}\n"
                         f"send_ocr_request_yandex обработан за {elapsed1}\n"
                         f"get_color_zones обработан за {elapsed2}")
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    st.text_area(label="Result", value=decision, height=40)
    col1, col2, col3 = st.columns([1, 1, 1], gap='medium')
    with col1:
        st.image(file, caption="Загруженное изображение")
    with col2:
        st.image(draw_rectangles_yandex(file,
                                        ocr_response['result']['textAnnotation']['blocks'],
                                        result_dict['sentences']),
                 caption="Обработанное изображение", use_column_width=True)
    with col3:
        st.image(image_with_zones_found, caption='Найденные зоны')


def on_upload_tesseract(file, temp: float):
    """ Вызывает обработку загруженного изображения и отображает результат """
    with st.spinner("Detecting image..."):
        try:
            start_time = time.time()  # засекаем время
            # get OCR result
            ocr_result, image_width, image_height = parse_image_tesseract(file)
            print(f"parse_image обработан за {elapsed_time(start_time, time.time())}")
            processed_result = process_image_tesseract(ocr_result, image_width, image_height, block_percentile)
            print(f"process_image обработан за {elapsed_time(start_time, time.time())}")
            metrics = parse_ocr_tesseract(processed_result)
            confidence = round(min(metrics[0] * 0.3 + metrics[1] * 0.05 + processed_result["blocks_overall"] * 0.07,
                                   1.0), 2)
            decision = "Переписка" if confidence >= temp else "Не переписка"
            decision += (f". Уверенность: {confidence} при уровне {temp}. "
                         f"Время выполнения: {elapsed_time(start_time, time.time())}")
        except Exception as e:
            print(f"Error: {e}")
            st.error(f"Error: {e}")
            st.stop()

    st.text_area(label="Result", value=decision, height=40)
    col1, col2 = st.columns([1, 1], gap='medium')
    with col1:
        st.image(file, caption="Загруженное изображение")
    with col2:
        st.image(draw_rectangles_tesseract(file, ocr_result, processed_result['text_blocks']),
                 caption="Обработанное изображение", use_column_width=True)


def main():
    """ Создает объекты streamlit-сервиса """
    uploader = st.file_uploader("Choose image for detection", type=['png', 'jpg', 'jpeg'])
    slider_value = st.empty()
    show_slider = st.checkbox("Настроить порог")
    if show_slider:
        slider_value = st.slider(
            'Threshold',
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            value=0.7
        )
    use_ocr = st.checkbox("Использовать OCR")
    if use_ocr:
        ocr_choosen = st.radio("Выберите OCR", ("Использовать YandexOCR", "Использовать Tesseract"))
        if ocr_choosen == "Использовать YandexOCR":
            folder_id = st.text_input("Введите folder_id")
            api_key = st.text_input("Введите API KEY")
    if uploader:
        temp = slider_value if isinstance(slider_value, float) else 0.7
        if use_ocr and ocr_choosen == "Использовать YandexOCR":
            if folder_id != "" and api_key != "":
                on_upload_yandex(uploader, temp, folder_id, api_key)
            else:
                st.error(f"Необходимо ввести действующие folder_id и api_key")
                st.stop()
        elif use_ocr and ocr_choosen == "Использовать Tesseract":
            on_upload_tesseract(uploader, temp)
        else:
            on_upload_without_ocr(uploader, temp)


def on_upload_without_ocr(file, temp: float):
    with st.spinner("Detecting image..."):
        try:
            start_time = time.time()  # засекаем время
            confidence, bounding_boxes, fill_im = process_image(file, block_percentile)
            elapsed = elapsed_time(start_time, time.time())
            print(f"process_image обработан за {elapsed}")
            decision = "Переписка" if confidence >= temp else "Не переписка"
            decision += (f". Уверенность: {confidence} при уровне {temp}. "
                         f"Время выполнения: {elapsed}\n")
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()
    st.text_area(label="Result", value=decision, height=40)
    col1, col2 = st.columns([1, 1], gap='medium')
    with col1:
        st.image(file, caption="Загруженное изображение")
    with col2:
        if fill_im is not None:
            st.image(plot_results(fill_im, bounding_boxes), caption="Обработанное изображение", use_column_width=True)


if __name__ == "__main__":
    main()
