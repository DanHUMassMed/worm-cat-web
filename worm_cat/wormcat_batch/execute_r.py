from subprocess import Popen, PIPE
import sys
import os
import platform
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

class ExecuteR(object):
    wormcat_r = '{}{}worm_cat.R'.format(os.path.dirname(__file__),os.path.sep)

    worm_cat_function = [wormcat_r,
                               '--file', 0,
                               '--title', 1,
                               '--out_dir', 2,
                               '--annotation_file',3,
                               '--input_type', 4
                               ]

    is_wormcat_installed = '{}{}is_wormcat_installed.R'.format(os.path.dirname(__file__),os.path.sep)
    wormcat_library_path = [is_wormcat_installed, '--no-save', 0, '--quiet', 1]

    if platform.system() == 'Windows':
        wormcat_library_path.insert(0,'rscript.exe')
        worm_cat_function.insert(0,'rscript.exe')


    def wormcat_library_path_fun(self):
        ret_val = self.run(self.wormcat_library_path,"")
        return ret_val

    def worm_cat_fun(self, file_name, out_dir, title="rgs", annotation_file="straight", input_type="Sequence ID"):
        logging.debug("worm_cat_fun: \n \tfile_name {}\n \tout_dir {}\n \ttitle {}\n \tannotation_file {}\n \tinput_type {}\n".format(
            file_name,out_dir,title,annotation_file, input_type
        ))
        ret_val = self.run(self.worm_cat_function, file_name, title, out_dir, annotation_file, input_type)
        return ret_val

    def run(self, arg_list, *args):
        try:
            processed_args = self.process_args(arg_list, *args)
            process = Popen(processed_args, stdout=PIPE)
            out, err = process.communicate()
            out = str(out, 'utf-8')
            if not out:
                out = None
            #sys.stderr.write("run: out={} err={}\n".format(out,err))
            return out
        except Exception as e:
            sys.stderr.write("ERROR: in execute_r {}\n".format(e))
            if "SoftTimeLimitExceeded()" == str(e):
                raise



    def process_args(self, arg_tuple, *args):
        # process the arg
        arg_list = list(arg_tuple)
        for index in range(0, len(arg_list)):
            if type(arg_list[index]) == int:
                # substitue for args passed in
                if arg_list[index] < len(args):
                    arg_list[index] = args[arg_list[index]]
                # if we have more substitutions than args passed delete the extras
                else:
                    del arg_list[index - 1:]
                    break
        return arg_list
