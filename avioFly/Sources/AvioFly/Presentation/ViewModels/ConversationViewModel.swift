import Foundation

@MainActor
final class ConversationViewModel: ObservableObject {
    @Published private(set) var messages: [ChatMessage] = []
    @Published private(set) var threads: [ConversationThread] = []
    @Published private(set) var isLoading = false
    @Published private(set) var errorMessage: String?
    @Published private(set) var activeMode: ConversationMode = .concierge
    @Published private(set) var assistantConfidence: Double = 0.0
    @Published private(set) var suggestedActions: [String] = []
    @Published private(set) var currentResponseKind: ChatResponseKind = .text
    @Published private(set) var currentOptions: [ChatOption] = []
    @Published private(set) var reasoningSummary: String = "Waiting for operational context."
    @Published private(set) var safetyNotice: String?
    @Published private(set) var artifacts: [ChatArtifact] = []
    @Published private(set) var isSendingMessage = false
    @Published private(set) var isLoadingMore = false
    @Published private(set) var hasMoreThreads = true

    private let chatService: ChatService
    private let conversationRepository: ConversationRepository
    private let conversationCache: ConversationCache
    private let conversationId = UUID().uuidString
    private let pageSize = 20
    private var nextCursor: String?
    private var currentSendTask: Task<Void, Never>?
    private let passengerProfile = PassengerProfile(
        loyaltyTier: nil,
        travelPreference: nil,
        accessibilityNeeds: []
    )

    init(
        conversationRepository: ConversationRepository,
        conversationCache: ConversationCache,
        chatService: ChatService
    ) {
        self.conversationRepository = conversationRepository
        self.conversationCache = conversationCache
        self.chatService = chatService
    }

    func selectMode(_ mode: ConversationMode) {
        activeMode = mode
    }

    func loadDashboard() async {
        isLoading = true
        errorMessage = nil

        do {
            // First page is the hot path; check memory before touching the repository.
            let page = ConversationPage(cursor: nil, limit: pageSize)
            if let cached = await conversationCache.cachedThreads(for: page) {
                threads = cached.items
                nextCursor = cached.nextCursor
                hasMoreThreads = cached.hasMore
                reasoningSummary = cached.items.isEmpty
                ? "No prior conversation threads loaded."
                : "Loaded \(cached.items.count) recent conversation thread(s) from cache."
                safetyNotice = "Connected to the conversation layer."
                isLoading = false
                return
            }

            let result = try await conversationRepository.loadThreads(page: page)
            threads = result.items
            nextCursor = result.nextCursor
            hasMoreThreads = result.hasMore
            await conversationCache.storeThreads(result, for: page)
            reasoningSummary = result.items.isEmpty
            ? "No prior conversation threads loaded."
            : "Loaded \(result.items.count) recent conversation thread(s)."
            safetyNotice = "Connected to the conversation layer."
        } catch {
            errorMessage = "Failed to load conversation data."
        }

        isLoading = false
    }

    func loadMoreThreads() async {
        guard hasMoreThreads, !isLoadingMore else { return }
        isLoadingMore = true
        defer { isLoadingMore = false }

        do {
            let page = ConversationPage(cursor: nextCursor, limit: pageSize)
            if let cached = await conversationCache.cachedThreads(for: page) {
                threads.append(contentsOf: cached.items)
                nextCursor = cached.nextCursor
                hasMoreThreads = cached.hasMore
                return
            }

            let result = try await conversationRepository.loadThreads(page: page)
            threads.append(contentsOf: result.items)
            nextCursor = result.nextCursor
            hasMoreThreads = result.hasMore
            await conversationCache.storeThreads(result, for: page)
        } catch {
            errorMessage = "Failed to load more conversation history."
        }
    }

    func sendMessage(_ text: String) async {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        guard currentSendTask == nil else { return }

        // Preserve an immediate local echo so the interface feels responsive even on slower backends.
        let userMessage = ChatMessage(
            id: UUID(),
            role: .user,
            content: trimmed,
            timestamp: Date(),
            status: .complete,
            artifacts: [],
            confidence: nil,
            isStreaming: false
        )
        messages.append(userMessage)
        errorMessage = nil
        isSendingMessage = true

        let request = ChatRequest(
            requestId: UUID(),
            conversationId: conversationId,
            userMessage: trimmed,
            context: ChatContext(
                localeIdentifier: Locale.current.identifier,
                passengerProfile: passengerProfile,
                applicationContext: [
                    "surface": "iPhone",
                    "module": "chat"
                ]
            ),
            requestedMode: activeMode,
            page: ConversationPage(cursor: nextCursor, limit: pageSize)
        )

        let cacheKey = "\(request.requestedMode.rawValue)::\(trimmed.lowercased())::\(request.page.cursor ?? "root")::\(request.page.limit)"

        if let cachedResponse = await conversationCache.cachedResponse(for: cacheKey) {
            // Replaying recent answers is useful during QA and when users repeat the same prompt.
            messages.append(
                ChatMessage(
                    id: UUID(),
                    role: .assistant,
                    content: cachedResponse.reply,
                    timestamp: Date(),
                    status: .complete,
                    artifacts: cachedResponse.artifacts,
                    confidence: cachedResponse.confidence,
                    isStreaming: false
                )
            )
            suggestedActions = cachedResponse.suggestedActions
            currentResponseKind = cachedResponse.kind
            currentOptions = cachedResponse.options
            reasoningSummary = cachedResponse.reasoningSummary
            safetyNotice = cachedResponse.safetyNotice
            assistantConfidence = cachedResponse.confidence
            artifacts = cachedResponse.artifacts
            isSendingMessage = false
            return
        }

        currentSendTask = Task { [chatService] in
            do {
                let response = try await chatService.send(request)
                await MainActor.run {
                    // Append only after decode succeeds to keep the transcript in order.
                    messages.append(
                        ChatMessage(
                            id: UUID(),
                            role: .assistant,
                            content: response.reply,
                            timestamp: Date(),
                            status: .complete,
                            artifacts: response.artifacts,
                            confidence: response.confidence,
                            isStreaming: false
                        )
                    )
                    suggestedActions = response.suggestedActions
                    currentResponseKind = response.kind
                    currentOptions = response.options
                    reasoningSummary = response.reasoningSummary
                    safetyNotice = response.safetyNotice
                    assistantConfidence = response.confidence
                    artifacts = response.artifacts
                    errorMessage = nil
                    isSendingMessage = false
                }
                await conversationCache.storeResponse(response, for: cacheKey)
            } catch is CancellationError {
                await MainActor.run {
                    isSendingMessage = false
                    errorMessage = "Request cancelled."
                }
            } catch {
                await MainActor.run {
                    isSendingMessage = false
                    errorMessage = "AI conversation service is temporarily unavailable."
                }
            }

            await MainActor.run {
                currentSendTask = nil
            }
        }
    }

    func cancelCurrentSend() {
        currentSendTask?.cancel()
        currentSendTask = nil
        isSendingMessage = false
    }

    func sendOption(_ option: ChatOption) async {
        // Options are forwarded as regular user prompts so the rest of the pipeline stays uniform.
        await sendMessage(option.value)
    }
}
