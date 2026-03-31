import Foundation

protocol ChatService {
    func send(_ request: ChatRequest) async throws -> ChatResponse
}

protocol StreamingChatService {
    func stream(_ request: ChatStreamRequest) -> AsyncThrowingStream<ChatStreamEvent, Error>
}

protocol ConversationRepository {
    func loadThreads(page: ConversationPage) async throws -> ConversationPageResult
}

protocol ConversationCache {
    func cachedThreads(for page: ConversationPage) async -> ConversationPageResult?
    func storeThreads(_ result: ConversationPageResult, for page: ConversationPage) async
    func cachedResponse(for key: String) async -> ChatResponse?
    func storeResponse(_ response: ChatResponse, for key: String) async
}

enum ChatStreamEvent: Equatable {
    case delta(String)
    case metadata(ChatResponse)
    case finished
}
