# central_executive

This is a workoing repo for TouchDesigner modules and other scripts created during Central Excecutive workshop in March 2018.

Some descriptions of files:

* `color_triggers.tox` - chromakey-based color trigger tox;
* `segmenter.tox` - TOX that utilizes [Semantic Image Segmentation Web Service](https://github.com/peetonn/tensorflow-deeplab-resnet/blob/master);
    requires `requests` module to be installed in TouchDesigner; works asynchronously;
* `style_transfer.tox` - TOX that utilized [Fast Style Transfer Web Service](https://github.com/peetonn/fast-style-transfer/blob/master);
    requires `requests` module to be installed in TouchDesigner; works asynchronously;
* `capture.tox` - TOX that captures video from video input and saves it into a file; these files can be read and played back using simple navigational UI;
* `system_status` - webservice that checks four services: OPT, OpenMoves, Segmener and Stlyer and outputs statuses in a simple dashboard.

> `.toe` files or files ending with `_example.tox` are example networks on how to use according tox files.
