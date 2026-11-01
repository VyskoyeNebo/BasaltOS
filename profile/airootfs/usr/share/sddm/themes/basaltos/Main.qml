import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: screen
    width: 1280; height: 800
    color: "#10232d"
    function login() { sddm.login(username.text, password.text, Math.max(0, sessions.currentIndex)) }
    Image { anchors.fill: parent; source: config.background; fillMode: Image.PreserveAspectCrop }
    Rectangle {
        anchors.centerIn: parent; width: 390; height: 430; radius: 18
        color: "#e810202b"; border.color: "#45616b"
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 35; spacing: 16
            Label { text: "BasaltOS"; color: "#f2eee8"; font.pixelSize: 34; font.bold: true }
            Label { text: "欢迎进入 Plasma 桌面"; color: "#b4c8cd"; font.pixelSize: 15 }
            Item { Layout.preferredHeight: 5 }
            TextField { id: username; text: "root"; placeholderText: "用户名"; Layout.fillWidth: true }
            TextField {
                id: password; placeholderText: "密码"; echoMode: TextInput.Password
                Layout.fillWidth: true; onAccepted: screen.login()
                Component.onCompleted: forceActiveFocus()
            }
            ComboBox { id: sessions; model: sessionModel; textRole: "name"; currentIndex: Math.max(0, sessionModel.lastIndex); Layout.fillWidth: true }
            Button { text: "登录"; highlighted: true; Layout.fillWidth: true; onClicked: screen.login() }
            Label { id: error; text: "Live 会话 · root"; color: "#b4c8cd"; font.pixelSize: 12 }
        }
    }
    Connections {
        target: sddm
        function onLoginFailed() { error.text = "登录失败，请重试"; password.text = ""; password.forceActiveFocus() }
    }
}
