// Sources/AffineEarthClientCLI/main.swift
// Public Thin Client Bridge for Affine.Earth (Contains ZERO Private Cell IP)
// Forwards stdio MCP JSON-RPC 2.0 or CLI prompts over HTTPS to https://affine.earth/v1/mcp

import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

@main
struct AffineEarthPublicClient {
    static let endpoint = URL(string: "https://affine.earth/v1/mcp")!

    static func main() async throws {
        while let line = readLine(strippingNewline: true) {
            guard !line.isEmpty else { continue }
            var req = URLRequest(url: endpoint)
            req.httpMethod = "POST"
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            req.setValue("1", forHTTPHeaderField: "X-Affine-No-Float")
            req.httpBody = Data(line.utf8)

            let (data, _) = try await URLSession.shared.data(for: req)
            if let out = String(data: data, encoding: .utf8) {
                print(out)
                fflush(stdout)
            }
        }
    }
}
