import os
import sqlite3
import sys
import glob
from tqdm import tqdm
from deepdanbooru.data.dataset import read_metadata_dict


def make_training_database(source_path, output_path, start_id, end_id,
                           use_deleted, chunk_size, overwrite, vacuum):
    '''
    Make sqlite database for training. Also add system tags.
    '''
    if source_path == output_path:
        raise Exception('Source path and output path is equal.')

    if os.path.exists(output_path):
        if overwrite:
            os.remove(output_path)
        else:
            raise Exception(f'{output_path} is already exists.')

    source_connection = sqlite3.connect(source_path)
    source_connection.row_factory = sqlite3.Row
    source_cursor = source_connection.cursor()

    output_connection = sqlite3.connect(output_path)
    output_connection.row_factory = sqlite3.Row
    output_cursor = output_connection.cursor()

    table_name = 'posts'
    id_column_name = 'id'
    md5_column_name = 'md5'
    extension_column_name = 'file_ext'
    tags_column_name = 'tag_string'
    tag_count_general_column_name = 'tag_count_general'
    rating_column_name = 'rating'
    score_column_name = 'score'
    deleted_column_name = 'is_deleted'

    # Create output table
    print('Creating table ...')
    output_cursor.execute(f"""CREATE TABLE {table_name} (
        {id_column_name} INTEGER NOT NULL PRIMARY KEY,
        {md5_column_name} TEXT,
        {extension_column_name} TEXT,
        {tags_column_name} TEXT,
        {tag_count_general_column_name} INTEGER )""")
    output_connection.commit()
    print('Creating table is complete.')

    current_start_id = start_id

    while True:
        print(
            f'Fetching source rows ... ({current_start_id}~)')
        source_cursor.execute(
            f"""SELECT
                {id_column_name},{md5_column_name},{extension_column_name},{tags_column_name},{tag_count_general_column_name},{rating_column_name},{score_column_name},{deleted_column_name}
            FROM {table_name} WHERE ({id_column_name} >= ?) ORDER BY {id_column_name} ASC LIMIT ?""",
            (current_start_id, chunk_size))

        rows = source_cursor.fetchall()

        if not rows:
            break

        insert_params = []

        for row in rows:
            post_id = row[id_column_name]
            md5 = row[md5_column_name]
            extension = row[extension_column_name]
            tags = row[tags_column_name]
            general_tag_count = row[tag_count_general_column_name]
            rating = row[rating_column_name]
            # score = row[score_column_name]
            is_deleted = row[deleted_column_name]

            if post_id > end_id:
                break

            if is_deleted and not use_deleted:
                continue

            if rating == 's':
                tags += f' rating:safe'
            elif rating == 'q':
                tags += f' rating:questionable'
            elif rating == 'e':
                tags += f' rating:explicit'

            # if score < -6:
            #     tags += f' score:very_bad'
            # elif score >= -6 and score < 0:
            #     tags += f' score:bad'
            # elif score >= 0 and score < 7:
            #     tags += f' score:average'
            # elif score >= 7 and score < 13:
            #     tags += f' score:good'
            # elif score >= 13:
            #     tags += f' score:very_good'

            insert_params.append(
                (post_id, md5, extension, tags, general_tag_count))

        if insert_params:
            print('Inserting ...')
            output_cursor.executemany(
                f"""INSERT INTO {table_name} (
                {id_column_name},{md5_column_name},{extension_column_name},{tags_column_name},{tag_count_general_column_name})
                values (?, ?, ?, ?, ?)""", insert_params)
            output_connection.commit()

        current_start_id = rows[-1][id_column_name] + 1

        if current_start_id > end_id or len(rows) < chunk_size:
            break

    if vacuum:
        print('Vacuum ...')
        output_cursor.execute('vacuum')
        output_connection.commit()

    source_connection.close()
    output_connection.close()


def make_training_database_metadata(data_meta, output_path, id_filter_list, start_id, end_id,
                                    use_deleted, chunk_size, overwrite, vacuum):
    print("Writing data_meta into output_path: \n\t{}".format(output_path))

    n_images = len(list(data_meta.keys()))
    print("\tThere are n = {} images".format(n_images))

    if os.path.exists(output_path):
        if overwrite:
            os.remove(output_path)
        else:
            print("\tIf table exists then inserting new rows")
    #             raise Exception(f'{output_path} is already exists.')

    # Connect
    output_connection = sqlite3.connect(output_path)
    output_connection.row_factory = sqlite3.Row
    output_cursor = output_connection.cursor()

    table_name = 'posts'
    id_column_name = 'id'
    md5_column_name = 'md5'
    extension_column_name = 'file_ext'
    tags_column_name = 'tag_string'
    tag_count_general_column_name = 'tag_count_general'
    rating_column_name = 'rating'
    score_column_name = 'score'
    deleted_column_name = 'is_deleted'

    # Create output table
    print('\tCreating table ...')
    output_cursor.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} (
        {id_column_name} INTEGER NOT NULL PRIMARY KEY,
        {md5_column_name} TEXT,
        {extension_column_name} TEXT,
        {tags_column_name} TEXT,
        {tag_count_general_column_name} INTEGER,
        {rating_column_name} TEXT,
        {score_column_name} FLOAT,
        {deleted_column_name} BOOL
        )""")
    output_connection.commit()
    print('\tCreating table is complete.')

    current_start_id = start_id

    # Hold
    insert_params = []

    # Skip if ID not found in image path
    if id_filter_list:
        print("\tFiltering metadata...")
        id_filter_set = set(id_filter_list)
        id_data_meta = set(data_meta.keys())
        id_data_meta_filtered = id_data_meta.intersection(id_filter_set)
        data_meta = {k: v for k, v in data_meta.items() if str(k) in id_data_meta_filtered}
        n_images = len(list(data_meta.keys()))
        print("\tFiltered metadata down to n = {}".format(n_images))

    # Preview
    print("\tParsing data meta")
    for i, (k, row) in enumerate(tqdm(data_meta.items())):

        post_id = row['id']
        md5 = row['md5']
        extension = row['file_ext']
        tags = row['tags']
        general_tag_count = len(tags)
        rating = row['rating']
        score = row['score']
        is_deleted = row['is_deleted']

        # Convert tags into a list of string with white space separated
        tags = [t['name'] for t in tags]
        tags = " ".join(tags)

        if is_deleted and not use_deleted:
            continue

        # Add rating to tags
        if rating == 's':
            tags += f' rating:safe'
        elif rating == 'q':
            tags += f' rating:questionable'
        elif rating == 'e':
            tags += f' rating:explicit'

        insert_params.append(
            (post_id, md5, extension, tags, general_tag_count, rating, score, is_deleted))

    if insert_params:
        print('\tInserting ...')
        output_cursor.executemany(
            f"""INSERT INTO {table_name} (
            {id_column_name},{md5_column_name},{extension_column_name},{tags_column_name},{tag_count_general_column_name},{rating_column_name},{score_column_name},{deleted_column_name})
            values (?, ?, ?, ?, ?, ?, ?, ?)""", insert_params)
        output_connection.commit()

    #     current_start_id = rows[-1][id_column_name] + 1

    if vacuum:
        print('\tVacuum ...')
        output_cursor.execute('vacuum')
        output_connection.commit()

    print("\tDone. Closing Connection.")
    output_connection.close()


def make_training_database_metadata_glob(
        data_meta_glob,
        output_path,
        image_path_glob=None,
        start_id=1,
        end_id=sys.maxsize,
        use_deleted=False,
        chunk_size=5000000,
        overwrite=True,
        vacuum=False):
    """
    Make training database from the danbooru metadata.
    """

    # Get Metadata files
    metadata_list = glob.glob(data_meta_glob)
    n_meta = len(metadata_list)
    print("metadata_list n = {}".format(n_meta))

    # Include IDs that have matching ID in image directory
    id_filter_list = None
    if image_path_glob:
        print("Filtering on IDs that have matching ID in image directory \n\t{}".format(image_path_glob))
        image_path_list = glob.glob(image_path_glob)
        id_filter_list = list()
        for img_path in image_path_list:
            # img path
            img_filename = os.path.basename(img_path)
            img_id, img_ext = os.path.splitext(img_filename)
            id_filter_list.append(img_id)
        id_filter_list = [str(id) for id in id_filter_list]
        print("Found image IDs \n\tn = {}".format(len(id_filter_list)))

    for i, metadata_file_path in enumerate(metadata_list):
        print("\tWorking on file [{} of {}] \n\t{}".format(i + 1, n_meta, metadata_file_path))

        # Read metadatafile
        data_meta = read_metadata_dict(metadata_file_path)

        # overwrite=True - Only overwrite the first creation, else append
        # overwrite=False - Append, but errors may happen if ID is non-unique
        overwrite_first = i == 0 if overwrite else False

        # Insert
        make_training_database_metadata(
            data_meta=data_meta,
            output_path=output_path,
            id_filter_list=id_filter_list,
            start_id=start_id,
            end_id=end_id,
            use_deleted=use_deleted,
            chunk_size=chunk_size,
            overwrite=overwrite_first,
            vacuum=vacuum
        )
