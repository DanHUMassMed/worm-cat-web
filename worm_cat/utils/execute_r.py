from subprocess import Popen, PIPE
import sys
import logging

logger = logging.getLogger(__name__)

class ExecuteR(object):

    def worm_cat_fun(self, file_name, out_dir, title="rgs", annotation_file="straight", input_type="Sequence ID"):

        ret_val = self.run(self.worm_cat_function, file_name, title, out_dir, annotation_file, input_type)

        return ret_val

    worm_cat_function = ('./worm_cat.R',
                               '--file', 0,
                               '--title', 1,
                               '--out_dir', 2,
                               '--annotation_file',3,
                               '--input_type', 4
                               )

    def run(self, arg_list, *args):
        try:
            processed_args = self.process_args(arg_list, *args)
            process = Popen(processed_args, stdout=PIPE)
            out, err = process.communicate()
            out = str(out, 'utf-8')
            if not out:
                out = '{}'
            logger.debug("run output: %s, err: %s", out, err)
            return out
        except Exception as e:
            logger.error("Command line error with args %s: %s", args, e, exc_info=True)
            sys.exit(-1)

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
