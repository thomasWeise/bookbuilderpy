"""Post-process PDF files."""

from os.path import exists, dirname

from bookbuilderpy.logger import logger
from bookbuilderpy.path import Path
from bookbuilderpy.shell import shell
from bookbuilderpy.versions import TOOL_GHOSTSCRIPT, has_tool


def pdf_postprocess(in_file: str,
                    out_file: str,
                    overwrite: bool = False) -> Path:
    """
    Post-process a pdf file.

    :param in_file: the input file
    :param out_file: the output file
    :param overwrite: should the output file be overwritten if it exists?
    :return: the output file
    """
    source = Path.file(in_file)
    output = Path.path(out_file)
    if (not overwrite) and exists(output):
        raise ValueError(f"Output file '{output}' already exists.")
    if source == output:
        raise ValueError(f"Input and output file is the same: '{source}'.")

    if has_tool(TOOL_GHOSTSCRIPT):
        logger(f"Post-processing pdf file '{source}' to '{output}' "
               f"by applying '{TOOL_GHOSTSCRIPT}'.")

        cmd = [TOOL_GHOSTSCRIPT,
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
        shell(cmd, timeout=600, cwd=dirname(source))
    else:
        logger(f"'{TOOL_GHOSTSCRIPT}' not installed, copying files directly.")
        Path.copy_file(source, output)

    output.enforce_file()

    return output
