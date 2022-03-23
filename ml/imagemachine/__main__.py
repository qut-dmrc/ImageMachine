import click
import yaml
import matplotlib.pyplot as plt
from .imagemachine import *

@click.command()
@click.option('-config','--config', nargs=1)
@click.option('-img','--img', nargs=1, default=None)
@click.option('-zip','---zip', nargs=1, default="")
@click.option('-metadata','--metadata', nargs=1, default=None)
@click.option('-fieldname','--fieldname', nargs=1, default=None)
@click.option('-d','--download', is_flag=True)
@click.option('-s','--size', nargs=1, default=None, type=int)
@click.option('-p','--pca', nargs=1, default=10, type=int)
@click.option('-k','--kclusters', nargs=1, default=16, type=int)
@click.option('-t','--time', is_flag=True)
@click.option('-size_list', 'size_list', nargs=1, default=None)
@click.option('-clustering', is_flag=True)
@click.option('-vgg16','--vgg16', nargs=1, default=None)
@click.option('-vgg19','--vgg19', nargs=1, default=None)
@click.option('-imgtofeat','--imgtofeat', nargs=1, default=None)
def main(config, img, _zip, metadata, fieldname, download, size, time, size_list, clustering, vgg16, vgg19, imgtofeat, pca, kclusters):
    # TODO: check
    if config:
        with open(os.path.join(os.getcwd(),config)) as f:
            params = yaml.full_load(f)
        download = params['download']
        img = params['img']   
        metadata = params['metadata']
        fieldname = params['fieldname']  
        size = params['size']      
        time = params['time']
        size_list = params['size_list']

    im = ImageMachine(pca,kclusters)
    if download:
        img = im.download_images(metadata, fieldname, size = size)
    if time:
        if size_list:
            size_list = size_list.strip().split(',')
            size_list = [int(i) for i in size_list]
            execution_time = im.time_process_images(size_list, img, _zip, metadata, fieldname)
            print(execution_time)
            plt.plot(size_list, execution_time)
            plt.xlabel('Data size')
            plt.ylabel('Execution time')
            plt.show()
    elif clustering:
        im.clustering(vgg16, vgg19, metadata, size, imgtofeat)
    else:
        im.process_images(img, _zip, metadata, fieldname, size)
    # # print(execution_time)
    # # # execution_time = [6.010409832000732, 24.725720405578613, 37.434375047683716, 50.046541929244995]
    # # plt.plot(data_size, execution_time)
    # # plt.xlabel('Data size')
    # # plt.ylabel('Execution time')
    # # plt.show()

if __name__ == "__main__":
    main()
