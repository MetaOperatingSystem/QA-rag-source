import Foundation
import CoreGraphics
import Vision

// usage: ocr <pdf> <out.txt> <startPage> <endPage> <dpi>
let A = CommandLine.arguments
guard A.count >= 6 else {
    FileHandle.standardError.write("usage: ocr <pdf> <out> <start> <end> <dpi>\n".data(using: .utf8)!)
    exit(2)
}
let pdfPath = A[1], outPath = A[2]
let startPage = Int(A[3]) ?? 1
let endPage   = Int(A[4]) ?? 1
let dpi       = CGFloat(Double(A[5]) ?? 200)

guard let doc = CGPDFDocument(URL(fileURLWithPath: pdfPath) as CFURL) else {
    FileHandle.standardError.write("cannot open pdf\n".data(using: .utf8)!)
    exit(3)
}
let total = doc.numberOfPages
let hi = min(endPage, total)

FileManager.default.createFile(atPath: outPath, contents: nil, attributes: nil)
guard let fh = FileHandle(forWritingAtPath: outPath) else { exit(4) }
func emit(_ s: String) { fh.write(s.data(using: .utf8)!) }

let scale = dpi / 72.0
var okPages = 0, emptyPages = 0

for p in startPage...hi {
    autoreleasepool {
        guard let page = doc.page(at: p) else { return }
        let box = page.getBoxRect(.mediaBox)
        let W = max(1, Int(box.width  * scale))
        let H = max(1, Int(box.height * scale))
        let cs = CGColorSpaceCreateDeviceRGB()
        guard let ctx = CGContext(data: nil, width: W, height: H, bitsPerComponent: 8,
                                  bytesPerRow: 0, space: cs,
                                  bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return }
        ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
        ctx.fill(CGRect(x: 0, y: 0, width: W, height: H))
        ctx.scaleBy(x: scale, y: scale)
        ctx.translateBy(x: -box.origin.x, y: -box.origin.y)
        ctx.drawPDFPage(page)
        guard let cg = ctx.makeImage() else { return }

        let req = VNRecognizeTextRequest()
        req.recognitionLevel = .accurate
        req.recognitionLanguages = ["zh-Hans", "en-US"]
        req.usesLanguageCorrection = true

        let handler = VNImageRequestHandler(cgImage: cg, options: [:])
        do { try handler.perform([req]) } catch { return }

        guard let obs = req.results, !obs.isEmpty else {
            emptyPages += 1
            emit("\n<<<PAGE \(p)>>>\n[无识别结果]\n")
            return
        }

        // 按视觉阅读顺序排序：先按行(y 降序, 容差 0.012), 同行按 x 升序
        let sorted = obs.sorted { a, b in
            let ay = a.boundingBox.origin.y, by = b.boundingBox.origin.y
            if abs(ay - by) > 0.012 { return ay > by }
            return a.boundingBox.origin.x < b.boundingBox.origin.x
        }
        var lines: [String] = []
        for o in sorted {
            if let t = o.topCandidates(1).first?.string {
                let s = t.trimmingCharacters(in: .whitespacesAndNewlines)
                if !s.isEmpty { lines.append(s) }
            }
        }
        emit("\n<<<PAGE \(p)>>>\n" + lines.joined(separator: "\n") + "\n")
        okPages += 1
        if p % 10 == 0 {
            FileHandle.standardError.write("p\(p)/\(hi)\n".data(using: .utf8)!)
        }
    }
}
fh.closeFile()
FileHandle.standardError.write("DONE \(startPage)-\(hi) ok=\(okPages) empty=\(emptyPages)\n".data(using: .utf8)!)
