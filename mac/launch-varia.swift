import Foundation

let bundleURL = Bundle.main.bundleURL
let resourcesdir = bundleURL.appendingPathComponent("Contents/Resources")

FileManager.default.changeCurrentDirectoryPath(resourcesdir.path)

let execPath = resourcesdir.appendingPathComponent("variamain").path

let args: [UnsafeMutablePointer<CChar>?] = [
    strdup("variamain"),
    nil
]

execv(execPath, args)