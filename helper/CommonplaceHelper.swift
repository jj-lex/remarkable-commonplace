// Commonplace helper: on-device Apple features for the Mac sync.
//   commonplace-helper ocr <image.png>   -> recognized text (handwriting or print), one line per line
//   commonplace-helper generate < input.json -> text from Apple's on-device model
//        input: {"system": "...", "prompt": "..."}
// Build: swiftc -O -o build/commonplace-helper helper/CommonplaceHelper.swift
import Foundation
import FoundationModels
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

struct GenerateInput: Decodable {
    let system: String
    let prompt: String
}

// Plain text generation with Apple's on-device model. Prompts are built by the sync, so every
// provider (Apple, Claude, OpenAI, ...) gets the same instructions.
func generate() async -> String {
    let data = FileHandle.standardInput.readDataToEndOfFile()
    guard let input = try? JSONDecoder().decode(GenerateInput.self, from: data) else { fail("bad generate input") }
    guard case .available = SystemLanguageModel.default.availability else { fail("Apple's on-device model is not available") }
    let session = LanguageModelSession(instructions: input.system)
    do { return try await session.respond(to: input.prompt).content } catch { fail("generate failed: \(error)") }
}

let args = CommandLine.arguments
guard args.count >= 2 else { fail("usage: commonplace-helper ocr <image>") }
switch args[1] {
case "ocr":
    guard args.count == 3 else { fail("usage: commonplace-helper ocr <image>") }
    print(recognize(args[2]))
case "generate":
    print(await generate())
default:
    fail("unknown command \(args[1])")
}
