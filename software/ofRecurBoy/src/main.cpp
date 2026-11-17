#include "ofMain.h"
#include "ofApp.h"
#include <cstdlib>
#include <string>

//========================================================================
int main( ){
    // Keep stock recurBOY logging unchanged. WAS uses notice-level logging
    // so repetitive GStreamer "unhandled message" verbose lines are hidden,
    // while warnings and errors remain visible.
    const char* wasMode = std::getenv("WAS_HEADLESS");
    if(wasMode && std::string(wasMode) == "1"){
        ofSetLogLevel(OF_LOG_NOTICE);
    }
    else{
        ofSetLogLevel(OF_LOG_VERBOSE);
    }
	//ofSetupOpenGL(1024,768, OF_WINDOW);			// <-------- setup the GL context
    //ofSetupOpenGL(1024,768, OF_WINDOW);
	ofGLESWindowSettings settings;
    settings.setSize(1280, 720);
	settings.setGLESVersion(2);
	ofCreateWindow(settings);


	// this kicks off the running of my app
	// can be OF_WINDOW or OF_FULLSCREEN
	// pass in width and height too:
	ofRunApp( new ofApp());


}
