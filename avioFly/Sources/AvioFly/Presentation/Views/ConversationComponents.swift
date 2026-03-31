import SwiftUI

struct IntelligenceBadgeView: View {
    let title: String
    let value: String
    let tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title.uppercased())
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
            Text(value)
                .font(.headline)
                .foregroundStyle(tint)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 18))
    }
}

struct OperationalModePillView: View {
    let mode: ConversationMode
    var body: some View {
        Text(mode.rawValue.capitalized)
            .font(.caption.weight(.semibold))
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(.blue.opacity(0.12), in: Capsule())
    }
}

struct ConversationBubbleView: View {
    let message: ChatMessage

    var body: some View {
        HStack(alignment: .bottom) {
            if message.role == .assistant {
                bubble
                Spacer(minLength: 28)
            } else {
                Spacer(minLength: 28)
                bubble
            }
        }
    }

    private var bubble: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                Text(message.role == .assistant ? "AI Copilot" : "Traveler")
                    .font(.caption.weight(.semibold))
                if let confidence = message.confidence {
                    Text("\(confidence * 100, specifier: "%.0f")% confidence")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                if message.isStreaming {
                    Text("Streaming")
                        .font(.caption2.weight(.semibold))
                        .foregroundStyle(.orange)
                }
            }
            Text(message.content)
                .font(.body)
            if !message.artifacts.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(message.artifacts) { artifact in
                        HStack {
                            Text(artifact.title)
                                .font(.caption.weight(.semibold))
                            Spacer()
                            Text(artifact.value)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
        }
        .padding()
        .background(
            message.role == .user
            ? LinearGradient(colors: [Color.blue.opacity(0.22), Color.blue.opacity(0.10)], startPoint: .topLeading, endPoint: .bottomTrailing)
            : LinearGradient(colors: [Color.gray.opacity(0.18), Color.gray.opacity(0.08)], startPoint: .topLeading, endPoint: .bottomTrailing),
            in: RoundedRectangle(cornerRadius: 18)
        )
    }
}

struct IntelligenceArtifactCardView: View {
    let artifact: ChatArtifact

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(artifact.kind.rawValue.uppercased())
                .font(.caption2.weight(.semibold))
                .foregroundStyle(.secondary)
            Text(artifact.title)
                .font(.headline)
            Text(artifact.value)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 16))
    }
}
