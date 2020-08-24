import os
import sqlite3
import glob


def load_tags(tags_path):
    with open(tags_path, 'r') as tags_stream:
        tags = [tag for tag in (tag.strip() for tag in tags_stream) if tag]
        return tags


def load_image_records(sqlite_path, minimum_tag_count, image_folder_path=None):
    if not os.path.exists(sqlite_path):
        raise Exception(f'SQLite database is not exists : {sqlite_path}')

    connection = sqlite3.connect(sqlite_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if image_folder_path is None:
        image_folder_path = os.path.join(os.path.dirname(sqlite_path), 'images')

    cursor.execute(
        """
        SELECT 
            md5, 
            file_ext, 
            tag_string 
        FROM 
            posts 
        WHERE 
            (file_ext = 'png' OR file_ext = 'jpg' OR file_ext = 'jpeg') 
            AND (tag_count_general >= ?) 
        ORDER BY 
            id
        """,
        (minimum_tag_count,))

    rows = cursor.fetchall()

    image_records = []

    for row in rows:
        md5 = row['md5']
        extension = row['file_ext']
        image_path = os.path.join(
            image_folder_path, md5[0:2], f'{md5}.{extension}')
        tag_string = row['tag_string']

        image_records.append((image_path, tag_string))

    connection.close()

    return image_records


def load_image_records_raw(sqlite_path, minimum_tag_count, image_folder_path=None):
    if not os.path.exists(sqlite_path):
        raise Exception(f'SQLite database is not exists : {sqlite_path}')

    connection = sqlite3.connect(sqlite_path)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if image_folder_path is None:
        image_folder_path = os.path.join(os.path.dirname(sqlite_path), 'images')

    # Make Image path lookup
    image_path_list = glob.glob(os.path.join(image_folder_path, "*/*"))
    image_dict = dict()
    for img_path in image_path_list:
        img_filename = os.path.basename(img_path)
        img_id, img_ext = os.path.splitext(img_filename)
        image_dict[img_id] = img_path

    cursor.execute(
        """
        SELECT 
            id,
            md5, 
            file_ext, 
            tag_string 
        FROM 
            posts 
        WHERE 
            (file_ext = 'png' OR file_ext = 'jpg' OR file_ext = 'jpeg') 
            AND (tag_count_general >= ?) 
        ORDER BY 
            id
        """,
        (minimum_tag_count,))

    rows = cursor.fetchall()

    image_records = []

    for row in rows:
        id = str(row['id'])
        md5 = row['md5']
        extension = row['file_ext']
        image_path = image_dict[id]
        tag_string = row['tag_string']

        image_records.append((image_path, tag_string))

    connection.close()

    return image_records
