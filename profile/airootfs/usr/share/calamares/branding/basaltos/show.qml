import QtQuick 2.15
import calamares.slideshow 1.0

Presentation {
    function onActivate() { currentSlide = 0 }
    function onLeave() {}
    Slide {
        Image {
            anchors.fill: parent
            source: "file:///usr/share/wallpapers/Next/contents/images/5120x2880.png"
            fillMode: Image.PreserveAspectCrop
        }
    }
}
