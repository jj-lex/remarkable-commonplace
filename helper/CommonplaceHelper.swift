// Commonplace helper: on-device Apple features for the Mac sync.
//   commonplace-helper ocr <image.png>   -> recognized text (handwriting or print), one line per line
// Build: swiftc -O -o build/commonplace-helper helper/CommonplaceHelper.swift
import Foundation
import Vision

func fail(_ msg: String) -> Never {
    FileHandle.standardError.write((msg + "\n").data(using: .utf8)!)
    exit(1)
}

func recognize(_ path: String) -> String {
    let url = URL(fileURLWithPath: path)
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.automaticallyDetectsLanguage = true
    let handler = VNImageRequestHandler(url: url, options: [:])
    do { try handler.perform([request]) } catch { fail("ocr failed: \(error)") }
    let observations = (request.results ?? []).sorted {
        // top to bottom (Vision's origin is bottom-left), then left to right
        abs($0.boundingBox.midY - $1.boundingBox.midY) > 0.02
            ? $0.boundingBox.midY > $1.boundingBox.midY
            : $0.boundingBox.minX < $1.boundingBox.minX
    }
    return observations.compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
}

let args = CommandLine.arguments
guard args.count >= 2 else { fail("usage: commonplace-helper ocr <image>") }
switch args[1] {
case "ocr":
    guard args.count == 3 else { fail("usage: commonplace-helper ocr <image>") }
    print(recognize(args[2]))
default:
    fail("unknown command \(args[1])")
}
