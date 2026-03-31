import Foundation

struct RemoteConversationService: ChatService {
    let endpoint: URL
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private let session: URLSession
    private let maxRetries: Int = 2

    init(endpoint: URL, session: URLSession = .shared) {
        self.endpoint = endpoint
        self.session = session
    }

    func send(_ request: ChatRequest) async throws -> ChatResponse {
        var urlRequest = URLRequest(url: endpoint)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.setValue(request.requestId.uuidString, forHTTPHeaderField: "X-Request-ID")
        urlRequest.httpBody = try encoder.encode(ConversationPayload(request: request))

        var lastError: Error?
        for attempt in 0...maxRetries {
            do {
                let (data, response) = try await session.data(for: urlRequest)
                guard let httpResponse = response as? HTTPURLResponse else {
                    throw ConversationServiceError.invalidResponse
                }
                try Self.validate(httpResponse)
                guard !data.isEmpty else { throw ConversationServiceError.emptyResponse }
                let envelope = try decoder.decode(ConversationResponse.self, from: data)
                return envelope.chat
            } catch is CancellationError {
                throw ConversationServiceError.cancelled
            } catch {
                lastError = error
                // Keep retry pressure low; the host app owns the broader provider strategy.
                if attempt < maxRetries {
                    try await Task.sleep(nanoseconds: UInt64(150_000_000 * (attempt + 1)))
                }
            }
        }

        throw lastError ?? URLError(.badServerResponse)
    }

    private static func validate(_ response: HTTPURLResponse) throws {
        switch response.statusCode {
        case 200..<300:
            return
        case 401, 403:
            throw ConversationServiceError.unauthorized
        case 429:
            throw ConversationServiceError.rateLimited
        case 500..<600:
            throw ConversationServiceError.serverUnavailable
        default:
            throw ConversationServiceError.invalidResponse
        }
    }
}

private struct ConversationPayload: Encodable {
    let conversationId: String
    let message: String
    let localeIdentifier: String
    let mode: String
    let accessibilityNeeds: [String]
    let applicationContext: [String: String]
    let pageCursor: String?
    let pageLimit: Int

    init(request: ChatRequest) {
        conversationId = request.conversationId
        message = request.userMessage
        localeIdentifier = request.context.localeIdentifier
        mode = request.requestedMode.rawValue
        accessibilityNeeds = request.context.passengerProfile?.accessibilityNeeds ?? []
        applicationContext = request.context.applicationContext
        pageCursor = request.page.cursor
        pageLimit = request.page.limit
    }
}

private struct ConversationResponse: Decodable {
    let chat: ChatResponse
}
