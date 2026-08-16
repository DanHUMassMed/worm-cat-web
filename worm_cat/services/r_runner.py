"""Unified R execution service for WormCat and WormCat Batch processing."""

import logging
import platform
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Any, List, Optional, Protocol, Sequence, Union, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class RRunnerProtocol(Protocol):
    """Structural protocol defining the contract for R execution runners."""

    def worm_cat_fun(
        self,
        file_name: str,
        out_dir: str,
        title: str = "rgs",
        annotation_file: str = "straight",
        input_type: str = "Sequence ID",
    ) -> Optional[str]:
        """Execute the WormCat R analysis script."""
        ...

    def wormcat_library_path_fun(self) -> Optional[str]:
        """Resolve the system path where the WormCat R library is installed."""
        ...


class ExecuteR:
    """Unified service for invoking R scripts (worm_cat.R, is_wormcat_installed.R)."""

    def __init__(self, base_dir: Optional[Union[str, Path]] = None) -> None:
        self.module_dir = Path(__file__).resolve().parent.parent
        self.base_dir = Path(base_dir) if base_dir else self.module_dir

        # Resolve paths to R script assets
        self.wormcat_r = str(self.module_dir / "worm_cat.R")

        installed_r = self.module_dir / "wormcat_batch" / "is_wormcat_installed.R"
        self.is_wormcat_installed = str(installed_r)

        self.worm_cat_function: List[Any] = [
            self.wormcat_r,
            "--file", 0,
            "--title", 1,
            "--out_dir", 2,
            "--annotation_file", 3,
            "--input_type", 4,
        ]

        self.wormcat_library_path: List[Any] = [
            self.is_wormcat_installed,
            "--no-save", 0,
            "--quiet", 1,
        ]

        if platform.system() == "Windows":
            self.wormcat_library_path.insert(0, "rscript.exe")
            self.worm_cat_function.insert(0, "rscript.exe")

    def wormcat_library_path_fun(self) -> Optional[str]:
        """Check if WormCat R package is installed and return its library path."""
        return self.run(self.wormcat_library_path, "")

    def worm_cat_fun(
        self,
        file_name: str,
        out_dir: str,
        title: str = "rgs",
        annotation_file: str = "straight",
        input_type: str = "Sequence ID",
    ) -> Optional[str]:
        """Run WormCat analysis on an input gene expression dataset."""
        logger.info(
            "Executing worm_cat: file_name=%s, out_dir=%s, title=%s, annotation_file=%s, input_type=%s",
            file_name,
            out_dir,
            title,
            annotation_file,
            input_type,
        )
        return self.run(self.worm_cat_function, file_name, title, out_dir, annotation_file, input_type)

    def run(self, arg_list: Sequence[Any], *args: Any) -> Optional[str]:
        """Execute the command line process and capture standard output."""
        try:
            processed_args = self.process_args(arg_list, *args)
            process = Popen(processed_args, stdout=PIPE, stderr=PIPE)
            out, err = process.communicate()
            out_str = out.decode("utf-8") if out else None
            err_str = err.decode("utf-8") if err else None

            if err_str:
                logger.debug("R execution stderr output: %s", err_str)
            return out_str
        except Exception as e:
            logger.error("Error executing R script with args %s: %s", args, e, exc_info=True)
            if "SoftTimeLimitExceeded" in type(e).__name__:
                raise
            raise RuntimeError(f"R script execution failed: {e}") from e

    def process_args(self, arg_tuple: Sequence[Any], *args: Any) -> List[str]:
        """Substitute positional argument placeholders in the command template."""
        arg_list = list(arg_tuple)
        for index in range(len(arg_list)):
            if isinstance(arg_list[index], int):
                idx = arg_list[index]
                if idx < len(args):
                    arg_list[index] = str(args[idx])
                else:
                    del arg_list[index - 1:]
                    break
            else:
                arg_list[index] = str(arg_list[index])
        return [str(item) for item in arg_list]
