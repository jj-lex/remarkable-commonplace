// Commonplace helper: on-device Apple features for the Mac sync.
//   commonplace-helper ocr <image.png>   -> recognized text (handwriting or print), one line per line
//   commonplace-helper topics < input.json -> 1-3 topics, comma-separated (Apple's on-device model)
//        input: {"passage": "...", "note": "...", "existing": ["topic", ...]}
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

struct TopicsInput: Decodable {
    let passage: String
    let note: String?
    let existing: [String]?
}

func topics() async -> String {
    let data = FileHandle.standardInput.readDataToEndOfFile()
    guard let input = try? JSONDecoder().decode(TopicsInput.self, from: data) else { fail("bad topics input") }
    guard case .available = SystemLanguageModel.default.availability else { fail("Apple's on-device model is not available") }
    var instructions = "A reader saves excerpts from books. For each excerpt, name what it is about: "
        + "the ideas, people, places or subjects in it. Answer with 1 to 3 lowercase subjects, "
        + "one or two ordinary English words each, separated by commas. No other text."
    if let existing = input.existing, !existing.isEmpty {
        instructions += " If one of these subjects fits, use it instead of a new one: " + existing.joined(separator: ", ") + "."
    }
    var prompt = "\(input.passage)"
    if let note = input.note, !note.isEmpty { prompt += "\n(The reader wrote: \(note))" }
    let session = LanguageModelSession(instructions: instructions)
    do { return try await session.respond(to: prompt).content } catch { fail("topics failed: \(error)") }
}

let args = CommandLine.arguments
guard args.count >= 2 else { fail("usage: commonplace-helper ocr <image>") }
switch args[1] {
case "ocr":
    guard args.count == 3 else { fail("usage: commonplace-helper ocr <image>") }
    print(recognize(args[2]))
case "topics":
    print(await topics())
default:
    fail("unknown command \(args[1])")
}
