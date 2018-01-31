from PIL import Image
import numpy as np
import datetime
import math
from data_viewer import DataViewer


start_date = "2017-10-01"
end_date = "2017-11-01"
start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
img_matrix = []
with open("symbol_list.txt", "r") as symbol_file:
    symbol_arr = symbol_file.read().split("\n")
    date_arr = []
    for symbol in symbol_arr:
        print(symbol)
        viewer = DataViewer()
        date_arr, value_list = viewer.get_daily_price(symbol, start_date, end_date, sparse=True)
        img_row = [0]*len(date_arr)
        offset = 0
        for value in value_list:
            if value is not None:
                img_row[offset] = 1
            offset += 1
        img_matrix.append(img_row)
    open("density.csv", "w").close()
    with open("density.csv", "a") as out_file:
        out_file.write('""')
        for date in date_arr:
            out_file.write(',"%s"' % date.strftime("%Y-%m-%d"))
        row_offset = 0
        for row in img_matrix:
            out_file.write("\n")
            out_file.write('"%s"' % symbol_arr[row_offset])
            for pixel in row:
                out_file.write(',"%s"' % str(pixel))
            row_offset = row_offset + 1
    img_matrix = np.array(img_matrix)*255
    scale = math.floor(img_matrix.shape[0] / img_matrix.shape[1])
    if scale > 4:
        img_matrix = img_matrix.repeat(scale, axis=1)
    img = Image.fromarray(img_matrix)
    img.convert('RGB').save("density.bmp")
    img.show()


