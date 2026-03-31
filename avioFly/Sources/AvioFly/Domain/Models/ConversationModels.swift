import Foundation

struct ChatMessage: Identifiable, Codable, Equatable {
    let id: UUID
    let role: ChatRole
    let content: String
    let timestamp: Date
    let status: ChatMessageStatus
    let artifacts: [ChatArtifact]
    let confidence: Double?
    let isStreaming: Bool
}

enum ChatRole: String, Codable, Equatable {
    case user
    case assistant
    case system
}

enum ChatMessageStatus: String, Codable, Equatable {
    case sending
    case streamed
    case complete
    case failed
}

struct ChatArtifact: Identifiable, Codable, Equatable {
    let id: UUID
    let title: String
    let value: String
    let kind: ChatArtifactKind
}

enum ChatArtifactKind: String, Codable, Equatable {
    case recommendation
    case rationale
    case signal
}

struct ChatRequest: Codable, Equatable {
    let requestId: UUID
    let conversationId: String
    let userMessage: String
    let context: ChatContext
    let requestedMode: ConversationMode
    let page: ConversationPage
}

struct ChatStreamRequest: Codable, Equatable {
    let request: ChatRequest
    let wantsDeltaUpdates: Bool
}

struct ChatContext: Codable, Equatable {
    let localeIdentifier: String
    let passengerProfile: PassengerProfile?
    let applicationContext: [String: String]
}

struct ChatResponse: Codable, Equatable {
    let kind: ChatResponseKind
    let reply: String
    let suggestedActions: [String]
    let options: [ChatOption]
    let confidence: Double
    let artifacts: [ChatArtifact]
    let reasoningSummary: String
    let safetyNotice: String?
    let streamingSupported: Bool
}

enum ChatResponseKind: String, Codable, Equatable {
    case text
    case options
    case mixed
}

struct ChatOption: Codable, Identifiable, Equatable {
    let id: String
    let title: String
    let value: String
}

enum ConversationMode: String, Codable, Equatable {
    case concierge
    case support
    case expert
}

struct PassengerProfile: Codable, Equatable {
    let loyaltyTier: String?
    let travelPreference: String?
    let accessibilityNeeds: [String]
}

struct ConversationThread: Identifiable, Codable, Equatable {
    let id: String
    let title: String
    let updatedAt: Date
    let preview: String?
}

struct ConversationPage: Codable, Equatable {
    let cursor: String?
    let limit: Int
}

struct ConversationPageResult: Codable, Equatable {
    let items: [ConversationThread]
    let nextCursor: String?
    let hasMore: Bool
}

enum ConversationServiceError: Error, Equatable {
    case cancelled
    case transportUnavailable
    case decodingFailed
    case invalidResponse
    case emptyResponse
    case rateLimited
    case unauthorized
    case serverUnavailable
}
