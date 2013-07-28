/*
 * simple key-stroke & mouse driven UI for WV (based on WebViewer/simpleUI.js)
 *
 * Notes: wv.sceneUpd should be set to 1 if the scene should rerendered
 *        wv.sgUpdate will be set to 1 if the sceneGraph has changed
 *                    should be set back to 0 after UI responds
 */

var openmdao = (typeof openmdao === "undefined" || !openmdao ) ? {} : openmdao ;

openmdao.WVCanvasFrame = function(wv, canvas_id, status_id) {
    /***********************************************************************
     *  private
     ***********************************************************************/

    // initialize private variables
    var _self = this,
        _canvas = document.getElementById(canvas_id),
        _statusline = new openmdao.StatusLine(status_id),
        _NO_MODIFIER = 0,
        _SHIFT_KEY   = 1,
        _ALT_KEY     = 2,
        _CTRL_KEY    = 4,
        _META_KEY    = 8,
        _WHEEL_DELTA = 120;

    // Event Handlers

    function getCursorXY(e) {
        if (!e) var e = event;
        wv.cursorX  = e.clientX;
        wv.cursorY  = e.clientY;
        wv.cursorX -= wv.offLeft+1;
        wv.cursorY  = wv.height-wv.cursorY+wv.offTop+1;

        wv.modifier = 0;
        if (e.shiftKey) wv.modifier |= _SHIFT_KEY;
        if (e.altKey)   wv.modifier |= _ALT_KEY;
        if (e.ctrlKey)  wv.modifier |= _CTRL_KEY;
        if (e.metaKey)  wv.modifier |= _CTRL_KEY;   // treat META same as CTRL
    }

    function getMouseDown(e) {
        if (!e) var e = event;
        wv.startX   = e.clientX;
        wv.startY   = e.clientY;
        wv.startX  -= wv.offLeft+1;
        wv.startY   = wv.height-wv.startY+wv.offTop+1;

        wv.dragging = true;
        wv.button   = e.button;
        wv.modifier = 0;
        if (e.shiftKey) wv.modifier |= _SHIFT_KEY;
        if (e.altKey)   wv.modifier |= _ALT_KEY;
        if (e.ctrlKey)  wv.modifier |= _CTRL_KEY;
        if (e.metaKey)  wv.modifier |= _CTRL_KEY;   // treat META same as CTRL
    }

    function getMouseUp(e) {
        wv.dragging = false;
    }

    function getKeyPress(e) {
        if (!e) var e = event;
        wv.keyPress = e.charCode;
    }

    function getMouseWheel(e) {
        if (!e) e=event;
        wv.wheelDelta = e.wheelDelta/_WHEEL_DELTA;
    }

    _canvas.addEventListener('mousemove',  getCursorXY,   false);
    _canvas.addEventListener('mousedown',  getMouseDown,  false);
    _canvas.addEventListener('mouseup',    getMouseUp,    false);
    _canvas.addEventListener('mousewheel', getMouseWheel, false);
    document.addEventListener('keypress',  getKeyPress,   false);

    /***********************************************************************
     *  privileged
     ***********************************************************************/

    // Required call-back functions

    this.wvUpdateCanvas = function(gl) {
        // Show the status line
        _statusline.snapshot();
    };

    this.wvInitUI = function() {
        // set up extra storage for matrix-matrix multiplies
        wv.uiMatrix = new J3DIMatrix4();

        // ui cursor variables
        wv.cursorX  = -1;             // current cursor position
        wv.cursorY  = -1;
        wv.keyPress = -1;             // last key pressed
        wv.startX   = -1;             // start of dragging position
        wv.startY   = -1;
        wv.button   = -1;             // button pressed
        wv.modifier =  0;             // modifier (shift,alt,cntl) bitflag
        wv.offTop   =  0;             // offset to upper-left corner of the canvas
        wv.offLeft  =  0;
        wv.dragging = false;
        wv.wheelDelta = 0;            // delta for mouse wheel
    };

    this.wvUpdateUI = function() {
        // deal with key presses
        if (wv.keyPress != -1) {
            console.log('WVCanvasFrame.wvUpdateUI keyPress:', wv.keyPress);
            switch(wv.keyPress) {
                case 42:                // '*' -- center the view
                    wv.centerV = 1;
                    break;
                case 60:                // '<' -- coarser tessellation
                    wv.socketUt.send("coarser");
                    break;
                case 62:                // '>' -- finer tessellation
                    wv.socketUt.send("finer");
                    break;
                case 76:                // 'L' -- locating state
                    if (wv.locate == 1) {
                        wv.locate = 0;
                    }
                    else {
                        wv.locate = 1;
                    }
                    break;
                case 80:                // 'P' -- picking state
                    if (wv.pick == 1) {
                        wv.pick     = 0;
                    }
                    else {
                        wv.pick     = 1;
                        wv.sceneUpd = 1;
                    }
                    break;
                case 99:                // 'c' -- color state
                    if (wv.active != undefined) {
                        wv.sceneGraph[wv.active].attrs ^= wv.plotAttrs.SHADING;
                        wv.sceneUpd = 1;
                    }
                    break;
                case 104:                // 'h' -- home (reset view transformation)
                    wv.mvMatrix.makeIdentity();
                    wv.scale    = 1.0;
                    wv.sceneUpd = 1;
                    break;
                case 108:                // 'l' -- line state
                    if (wv.active != undefined) {
                        wv.sceneGraph[wv.active].attrs ^= wv.plotAttrs.LINES;
                        wv.sceneUpd = 1;
                    }
                    break;
                case 110:                // 'n' -- next active
                    for (var gprim in wv.sceneGraph) {
                        if (wv.active == undefined) {
                            wv.active = gprim;
                            break;
                        }
                        if (wv.active == gprim) {
                            wv.active = undefined;
                        }
                    }
                    break;
                case 111:                // 'o' -- orientation state
                    if (wv.active != undefined) {
                        wv.sceneGraph[wv.active].attrs ^= wv.plotAttrs.ORIENTATION;
                        wv.sceneUpd = 1;
                    }
                    break;
                case 112:                // 'p' -- point state
                    if (wv.active != undefined) {
                        wv.sceneGraph[wv.active].attrs ^= wv.plotAttrs.POINTS;
                        wv.sceneUpd = 1;
                    }
                    break;
                case 114:                // 'r' -- render state
                    if (wv.active != undefined) {
                        wv.sceneGraph[wv.active].attrs ^= wv.plotAttrs.ON;
                        wv.sceneUpd = 1;
                    }
                    break;
                case 115:                // 's' -- set active to picked
                    if (wv.picked != undefined) {
                        wv.active = wv.picked.gprim;
                    }
                    break;
                case 116:                // 't' -- transparent state
                    if (wv.active != undefined) {
                        wv.sceneGraph[wv.active].attrs ^= wv.plotAttrs.TRANSPARENT;
                        wv.sceneUpd = 1;
                    }
                    break;
            }
        }

        wv.keyPress = -1;

        // UI is in screen coordinates (not object)
        wv.uiMatrix.load(wv.mvMatrix);
        wv.mvMatrix.makeIdentity();

        if (wv.wheelDelta !== 0) {
            var scale = Math.exp(wv.wheelDelta/16.0);
            wv.mvMatrix.scale(scale, scale, scale);
            wv.scale     *= scale;
            wv.sceneUpd   = 1;
            wv.wheelDelta = 0;
        }

        // now mouse movement
        if (wv.dragging) {
            // cntrl is down
            if (wv.modifier == _CTRL_KEY) {
                var angleX =  (wv.startY-wv.cursorY)/4.0;
                var angleY = -(wv.startX-wv.cursorX)/4.0;
                if ((angleX != 0.0) || (angleY != 0.0)) {
                    wv.mvMatrix.rotate(angleX, 1,0,0);
                    wv.mvMatrix.rotate(angleY, 0,1,0);
                    wv.sceneUpd = 1;
                }
            }

            // alt is down
            if (wv.modifier == _ALT_KEY) {
                var xf = wv.startX - wv.width/2;
                var yf = wv.startY - wv.height/2;
                if ((xf != 0.0) || (yf != 0.0)) {
                    var theta1 = Math.atan2(yf, xf);
                    xf = wv.cursorX - wv.width/2;
                    yf = wv.cursorY - wv.height/2;
                    if ((xf != 0.0) || (yf != 0.0)) {
                        var dtheta = Math.atan2(yf, xf)-theta1;
                        if (Math.abs(dtheta) < 1.5708) {
                            var angleZ = 128*(dtheta)/3.1415926;
                            wv.mvMatrix.rotate(angleZ, 0,0,1);
                            wv.sceneUpd = 1;
                        }
                    }
                }
            }

            // shift is down
            if (wv.modifier == _SHIFT_KEY) {
                if (wv.cursorY != wv.startY) {
                    var scale = Math.exp((wv.cursorY-wv.startY)/512.0);
                    wv.mvMatrix.scale(scale, scale, scale);
                    wv.scale   *= scale;
                    wv.sceneUpd = 1;
                }
            }

            // no modifier
            if (wv.modifier == _NO_MODIFIER) {
                var transX = (wv.cursorX-wv.startX)/256.0;
                var transY = (wv.cursorY-wv.startY)/256.0;
                if ((transX != 0.0) || (transY != 0.0)) {
                    wv.mvMatrix.translate(transX, transY, 0.0);
                    wv.sceneUpd = 1;
                }
            }

            wv.startX = wv.cursorX;
            wv.startY = wv.cursorY;
        }
    };


    this.wvUpdateView = function() {
        wv.mvMatrix.multiply(wv.uiMatrix);
    };

    this.wvServerMessage = function(text) {
        wv.logger(" Server Message: " + text);
    };

    //
    // needed when the canvas size changes or relocates
    this.reshape = function(gl) {
        if (wv.offTop != _canvas.offsetTop || wv.offLeft != _canvas.offsetLeft) {
            wv.offTop  = _canvas.offsetTop;
            wv.offLeft = _canvas.offsetLeft;
        }

        var windowWidth  = window.innerWidth  - 20;
        var windowHeight = window.innerHeight - 40;
        if (windowWidth == wv.width && windowHeight == wv.height) {
            return;
        }

        wv.width       = windowWidth;
        wv.height      = windowHeight;
        _canvas.width  = wv.width;
        _canvas.height = wv.height;

        // Set the viewport and perspective matrix for the scene
        gl.viewport(0, 0, wv.width, wv.height);
        wv.perspectiveMatrix = new J3DIMatrix4();
        wv.sceneUpd = 1;

        wv.InitDraw();
    };

    // put out a cursor
    this.jack = function(gl, x,y,z, delta) {
        if (wv.sceneGraph["jack"] != undefined) {
            wv.deleteGPrim(gl, "jack");
            delete wv.sceneGraph["jack"];
        }

        var vertices = new Float32Array(18);
        for (var i = 0; i < 6; i++) {
            vertices[3*i  ] = x;
            vertices[3*i+1] = y;
            vertices[3*i+2] = z;
        }
        vertices[ 0] -= delta;
        vertices[ 3] += delta;
        vertices[ 7] -= delta;
        vertices[10] += delta;
        vertices[14] -= delta;
        vertices[17] += delta;

        var vbo = wv.createVBO(gl, vertices, undefined, undefined, undefined);
        wv.sceneGraph["jack"] = createGPrim(1, 1, wv.plotAttrs.ON);
        wv.sceneGraph["jack"].lines[0]  = vbo;
        wv.sceneGraph["jack"].lineWidth = 3;
        wv.sceneGraph["jack"].lColor    = [0.0, 0.0, 1.0];
    };
}

/*
 * Status Line
 *
 * This object keeps track of framerate plus other wv data and displays it as
 * the innerHTML text of the HTML element with the passed id. Once created you
 * call snapshot at the end of every rendering cycle. Every 500ms the framerate
 * is updated in the HTML element.
 */

openmdao.StatusLine = function(id) {
    /***********************************************************************
     *  private
     ***********************************************************************/
    var _self = this,
        _elem = document.getElementById(id),
        _numFramerates = 10,
        _framerateUpdateInterval = 500,
        _renderTime = -1,
        _framerates = [ ];

    function updateFramerate() {
        var tot = 0;
        for (var i = 0; i < _framerates.length; ++i) {
            tot += _framerates[i];
        }

        var framerate = Math.round(tot / _framerates.length);
        var string = "Framerate:"+framerate+"fps";
        if (wv.picked != undefined) {
            string = string+"&nbsp; &nbsp; &nbsp; Picked: "+wv.picked.gprim+
                     "  strip = "+wv.picked.strip+"  type = "+wv.picked.type;
        }
        if (wv.active != undefined) {
            string = string+"&nbsp; &nbsp; &nbsp; Active: "+wv.active;
        }
        if (wv.located != undefined) {
            string = string+"&nbsp; &nbsp; &nbsp; ("+wv.located[0]+", &nbsp; "+
                     wv.located[1]+", &nbsp; "+wv.located[2]+")";
        }

        _elem.innerHTML = string
    }

    setInterval(updateFramerate, _framerateUpdateInterval);

    /***********************************************************************
     *  privileged
     ***********************************************************************/

    this.snapshot = function() {
        if (_renderTime < 0) {
            _renderTime = new Date().getTime();
        }
        else {
            var newTime = new Date().getTime();
            var t = newTime - _renderTime;
            if (t == 0) {
                return;
            }
            var framerate = 1000/t;
            _framerates.push(framerate);
            while(_framerates.length > _numFramerates) {
                _framerates.shift();
            }
            _renderTime = newTime;
        }
    }
}




