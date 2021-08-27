"""Post-process PDF files."""

import subprocess  # nosec
from os.path import exists, dirname

from bookbuilderpy.logger import log
from bookbuilderpy.path import Path


def pdf_postprocess(in_file: str,
                    out_file: str,
                    overwrite: bool = False) -> Path:
    """
    Post-process a pdf file.

    :param str in_file: the input file
    :param str out_file: the output file
    :param bool overwrite: should the output file be overwritten if it exists?
    :return: the output file
    :rtype: Path
    """
    source = Path.file(in_file)
    output = Path.path(out_file)
    if (not overwrite) and exists(output):
        raise ValueError(f"Output file '{output}' already exists.")

    log(f"Post-processing pdf file '{source}' to '{output}'.")

    cmd = ["gs",
           "-q",
           "-dPrinted=false",
           "-dEmbedAllFonts=true",
           "-dSubsetFonts=true",
           "-dCompressFonts=true",
           "-dCompressStreams=true",
           "-dOptimize=true",
           "-dUNROLLFORMS",
           "-dCompatibilityLevel=1.7",
           "-dLZWEncodePages=true",
           "-dCompressPages=true",
           "-dPassThroughJPEGImages=true",
           "-dPassThroughJPXImages=true",
           "-dCannotEmbedFontPolicy=/Error",
           "-dPreserveCopyPage=false",
           "-dPreserveEPSInfo=false",
           "-dPreserveHalftoneInfo=false",
           "-dPreserveOPIComments=false",
           "-dPreserveOverprintSettings=false",
           "-dPreserveSeparation=false",
           "-dPreserveDeviceN=false",
           "-dMaxBitmap=2147483647",
           "-dDownsampleMonoImages=false",
           "-dDownsampleGrayImages=false",
           "-dDownsampleColorImages=false",
           "-dDetectDuplicateImages=true",
           "-dHaveTransparency=true",
           "-dAutoFilterColorImages=false",
           "-dAutoFilterGrayImages=false",
           "-dColorImageFilter=/FlateEncode",
           "-dGrayImageFilter=/FlateEncode",
           "-dColorConversionStrategy=/LeaveColorUnchanged",
           "-dFastWebView=false",
           "-dNOPAUSE",
           "-dQUIET",
           "-dBATCH",
           "-dSAFER",
           "-sDEVICE=pdfwrite",
           "-dAutoRotatePages=/PageByPage",
           f'-sOutputFile="{output}"',
           source,
           '-c "<</NeverEmbed [ ]>> setdistillerparams"']
    ret = subprocess.run(cmd, check=True, text=True, timeout=600,  # nosec
                         cwd=Path.directory(dirname(source)))  # nosec
    if ret.returncode != 0:
        raise ValueError(
            f"Error when executing pandoc command '{cmd}'.")
    output.enforce_file()

    return output
