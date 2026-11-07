// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "AffineEarthClient",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(name: "affine-earth-client", targets: ["AffineEarthClientCLI"])
    ],
    targets: [
        .executableTarget(
            name: "AffineEarthClientCLI",
            path: "Sources/AffineEarthClientCLI"
        )
    ]
)
