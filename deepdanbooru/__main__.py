import sys

import click

import deepdanbooru as dd

import tensorflow as tf

# Devices
physical_devices = [dev.name.replace("/physical_device:", "") for dev in tf.config.list_physical_devices()]
gpu_devices_names = [dev for dev in physical_devices if dev[:3] == 'GPU']
cpu_devices_names = [dev for dev in physical_devices if dev[:3] == 'CPU']
print("===== GPU Devices are: {}".format(gpu_devices_names))
print("===== CPU Devices are: {}".format(cpu_devices_names))

# Fixes CUDNN error on GPU
gpu_devices = tf.config.experimental.list_physical_devices('GPU')
if len(gpu_devices):
    config = tf.config.experimental.set_memory_growth(gpu_devices[0], True)

__version__ = '1.1.0'


@click.version_option(prog_name='DeepDanbooru', version=__version__)
@click.group()
def main():
    '''
    AI based multi-label girl image classification system, implemented by using TensorFlow.
    '''
    pass


@main.command('create-project')
@click.argument('project_path', type=click.Path(exists=False, resolve_path=True, file_okay=False, dir_okay=True))
def create_project(project_path):
    dd.commands.create_project(project_path)


@main.command('download-tags')
@click.option('--limit', default=10000, help='Limit for each category tag count.')
@click.option('--minimum-post-count', default=500, help='Minimum post count for tag.')
@click.option('--overwrite', help='Overwrite tags if exists.', is_flag=True)
@click.argument('path', type=click.Path(exists=False, resolve_path=True, file_okay=False, dir_okay=True))
def download_tags(path, limit, minimum_post_count, overwrite):
    dd.commands.download_tags(path, limit, minimum_post_count, overwrite)


@main.command('make-training-database-metadata')
@click.argument('data_meta_glob', nargs=1, required=True)
@click.argument('output_path', type=click.Path(exists=False, resolve_path=True, file_okay=True, dir_okay=False), nargs=1, required=True)
@click.option('--image_path_glob', default=None, help='glob to path of images to filter out IDs', )
@click.option('--start-id', default=1, help='Start id.', )
@click.option('--end-id', default=sys.maxsize, help='End id.')
@click.option('--use-deleted', help='Use deleted posts.', is_flag=True)
@click.option('--chunk-size', default=5000000, help='Chunk size for internal processing.')
@click.option('--overwrite', help='Overwrite tags if exists.', is_flag=True)
@click.option('--vacuum', help='Execute VACUUM command after making database.', is_flag=True)
def make_training_database_metadata(data_meta_glob, output_path, image_path_glob, start_id, end_id, use_deleted, chunk_size, overwrite, vacuum):
    dd.commands.make_training_database_metadata_glob(data_meta_glob, output_path, image_path_glob, start_id, end_id,
                                       use_deleted, chunk_size, overwrite, vacuum)


@main.command('make-training-database')
@click.argument('source_path', type=click.Path(exists=True, resolve_path=True, file_okay=True, dir_okay=False), nargs=1, required=True)
@click.argument('output_path', type=click.Path(exists=False, resolve_path=True, file_okay=True, dir_okay=False), nargs=1, required=True)
@click.option('--start-id', default=1, help='Start id.', )
@click.option('--end-id', default=sys.maxsize, help='End id.')
@click.option('--use-deleted', help='Use deleted posts.', is_flag=True)
@click.option('--chunk-size', default=5000000, help='Chunk size for internal processing.')
@click.option('--overwrite', help='Overwrite tags if exists.', is_flag=True)
@click.option('--vacuum', help='Execute VACUUM command after making database.', is_flag=True)
def make_training_database(source_path, output_path, start_id, end_id, use_deleted, chunk_size, overwrite, vacuum):
    dd.commands.make_training_database(source_path, output_path, start_id, end_id,
                                       use_deleted, chunk_size, overwrite, vacuum)


@main.command('train-project')
@click.argument('project_path', type=click.Path(exists=True, resolve_path=True, file_okay=False, dir_okay=True))
def train_project(project_path):
    dd.commands.train_project(project_path)


@main.command('evaluate-project', help='Evaluate the project. If the target path is folder, it evaulates all images recursively.')
@click.argument('project_path', type=click.Path(exists=True, resolve_path=True, file_okay=False, dir_okay=True))
@click.argument('target_path', type=click.Path(exists=True, resolve_path=True, file_okay=True, dir_okay=True))
@click.option('--threshold', help='Threshold for tag estimation.', default=0.5)
def evaluate_project(project_path, target_path, threshold):
    dd.commands.evaluate_project(project_path, target_path, threshold)


@main.command('grad-cam', help='Experimental feature. Calculate activation map using Grad-CAM.')
@click.argument('project_path', type=click.Path(exists=True, resolve_path=True, file_okay=False, dir_okay=True))
@click.argument('target_path', type=click.Path(exists=True, resolve_path=True, file_okay=True, dir_okay=True))
@click.argument('output_path', type=click.Path(resolve_path=True, file_okay=False, dir_okay=True), default='.')
@click.option('--threshold', help='Threshold for tag estimation.', default=0.5)
def grad_cam(project_path, target_path, output_path, threshold):
    dd.commands.grad_cam(project_path, target_path, output_path, threshold)


@main.command('evaluate', help='Evaluate model by estimating image tag.')
@click.argument('target_paths', nargs=-1, type=click.Path(exists=True, resolve_path=True, file_okay=True, dir_okay=True))
@click.option('--project-path', type=click.Path(exists=True, resolve_path=True, file_okay=False, dir_okay=True),
              help='Project path. If you want to use specific model and tags, use --model-path and --tags-path options.')
@click.option('--model-path', type=click.Path(exists=True, resolve_path=True, file_okay=True, dir_okay=False))
@click.option('--tags-path', type=click.Path(exists=True, resolve_path=True, file_okay=True, dir_okay=False))
@click.option('--threshold', default=0.5)
@click.option('--allow-gpu', default=False, is_flag=True)
@click.option('--compile/--no-compile', 'compile_model', default=False)
@click.option('--allow-folder', default=False, is_flag=True, help='If this option is enabled, TARGET_PATHS can be folder path and all images (using --folder-filters) in that folder is estimated recursively. If there are file and folder which has same name, the file is skipped and only folder is used.')
@click.option('--folder-filters', default='*.[Pp][Nn][Gg],*.[Jj][Pp][Gg],*.[Jj][Pp][Ee][Gg],*.[Gg][Ii][Ff]', help='Glob pattern for searching image files in folder. You can specify multiple patterns by separating comma. This is used when --allow-folder is enabled. Default:*.[Pp][Nn][Gg],*.[Jj][Pp][Gg],*.[Jj][Pp][Ee][Gg],*.[Gg][Ii][Ff]')
@click.option('--verbose', default=False, is_flag=True)
@click.option('--output-csv', type=click.Path(exists=False, resolve_path=True, file_okay=True, dir_okay=False), default=None)
def evaluate(target_paths, project_path, model_path, tags_path, threshold, allow_gpu, compile_model, allow_folder, folder_filters, verbose, output_csv):
    dd.commands.evaluate(target_paths, project_path, model_path, tags_path, threshold, allow_gpu, compile_model, allow_folder, folder_filters, verbose, output_csv)


if __name__ == '__main__':
    main()
