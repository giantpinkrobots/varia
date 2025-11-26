import Foundation

let bundleURL = Bundle.main.bundleURL
let resourcesdir = bundleURL.appendingPathComponent("Contents/Resources")

FileManager.default.changeCurrentDirectoryPath(resourcesdir.path)

let execPath = resourcesdir.appendingPathComponent("Varia").path

let args: [UnsafeMutablePointer<CChar>?] = [
    strdup("Varia"),
    nil
]

execv(execPath, args)