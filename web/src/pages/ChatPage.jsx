import React from "react";
import { AlertTriangle, ArrowUp, BookOpen, Loader2, RotateCcw, Stethoscope } from "lucide-react";
import { sendChat } from "../api";

const initialMessages = [
  {
    role: "assistant",
    content: "您好，我是 AI 医生助手。请描述您的症状、持续时间、年龄性别、既往病史和已经做过的检查。",
  },
];

function renderInline(text) {
  const parts = [];
  const pattern = /\*\*(.+?)\*\*/g;
  let lastIndex = 0;
  let match;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index).replace(/\*/g, ""));
    }
    parts.push(<strong key={`${match.index}-${match[1]}`}>{match[1]}</strong>);
    lastIndex = pattern.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex).replace(/\*/g, ""));
  }

  return parts;
}

function cleanLine(rawLine) {
  let line = rawLine.trim();
  line = line.replace(/^--+$/, "---");
  line = line.replace(/^\*+\s*(\d+[.)])/g, "$1");
  line = line.replace(/^\*(.+)\*\*$/, "**$1**");
  line = line.replace(/\*\*([^*]+)$/g, "$1");
  line = line.replace(/^\*([^*]+)$/g, "$1");
  line = line.replace(/\*\*/g, "");
  return line.trim();
}

function FormattedMessage({ content }) {
  const lines = content.split("\n");
  const blocks = [];
  let listItems = [];
  let listType = null;

  const flushList = () => {
    if (!listItems.length) return;
    const Tag = listType === "ordered" ? "ol" : "ul";
    blocks.push(
      <Tag className="message-list" key={`list-${blocks.length}`}>
        {listItems.map((item, index) => (
          <li key={`${item}-${index}`}>{renderInline(item)}</li>
        ))}
      </Tag>
    );
    listItems = [];
    listType = null;
  };

  lines.forEach((rawLine, index) => {
    const line = cleanLine(rawLine);
    if (!line) {
      flushList();
      return;
    }

    if (line === "---") {
      flushList();
      blocks.push(<hr className="message-divider" key={`divider-${index}`} />);
      return;
    }

    const heading = line.match(/^#{1,4}\s*(.+)$/);
    if (heading) {
      flushList();
      blocks.push(
        <h3 className="message-heading" key={`heading-${index}`}>
          {renderInline(heading[1])}
        </h3>
      );
      return;
    }

    const boldHeading = line.match(/^\*\*(.+?)\*\*[:：]?$/);
    const shortColonHeading = line.length <= 34 && /[:：]$/.test(line);
    if (boldHeading || shortColonHeading) {
      flushList();
      blocks.push(
        <h3 className="message-heading" key={`smart-heading-${index}`}>
          {renderInline(boldHeading ? boldHeading[1] : line.replace(/[:：]$/, ""))}
        </h3>
      );
      return;
    }

    const bullet = line.match(/^(?:[-*•]|[*]\s{2,})\s*(.+)$/);
    if (bullet) {
      if (listType !== "unordered") flushList();
      listType = "unordered";
      listItems.push(bullet[1].trim());
      return;
    }

    const ordered = line.match(/^(?:\d+[.)]|[（(]?\d+[）)])\s*(.+)$/);
    if (ordered) {
      if (listType !== "ordered") flushList();
      listType = "ordered";
      listItems.push(ordered[1].trim());
      return;
    }

    const questionLike = /[？?]$/.test(line) || /^(是否|有没有|有无|什么|多久|哪里|如何|哪种|最近)/.test(line);
    if (questionLike && line.length <= 90) {
      if (listType !== "unordered") flushList();
      listType = "unordered";
      listItems.push(line);
      return;
    }

    flushList();
    blocks.push(
      <p key={`paragraph-${index}`}>
        {renderInline(line.replace(/^[:：]\s*/, ""))}
      </p>
    );
  });

  flushList();
  return <div className="message-content">{blocks}</div>;
}

function MessageBubble({ message }) {
  return (
    <article className={`message ${message.role}`}>
      <div className="message-meta">{message.role === "user" ? "你" : "AI 医生"}</div>
      <FormattedMessage content={message.content} />
    </article>
  );
}

function ReferenceList({ references }) {
  if (!references.length) {
    return (
      <div className="empty-state compact">
        <BookOpen size={20} />
        <p>发送症状后会自动显示相似病例参考。</p>
      </div>
    );
  }

  return (
    <div className="reference-list">
      {references.map((item) => (
        <article className="reference-card" key={item.id}>
          <div className="reference-head">
            <strong>#{item.id}</strong>
            <span>参考病例</span>
          </div>
          <h3>{item.title || item.department || "未命名病例"}</h3>
          <p>{item.chief_complaint || "暂无主诉"}</p>
          <small>{item.diagnosis || item.diseases || "暂无诊断"}</small>
        </article>
      ))}
    </div>
  );
}

export default function ChatPage({ health }) {
  const [messages, setMessages] = React.useState(initialMessages);
  const [input, setInput] = React.useState("");
  const [references, setReferences] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");

  const canSend = input.trim().length > 0 && !loading;

  const submit = async (event) => {
    event.preventDefault();
    if (!canSend) return;

    const userMessage = { role: "user", content: input.trim() };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    setError("");

    try {
      const result = await sendChat(userMessage.content, nextMessages.filter((item) => item.role !== "system"));
      setReferences(result.references || []);
      setMessages([...nextMessages, { role: "assistant", content: result.reply }]);
    } catch (err) {
      setError(err.message);
      setMessages(nextMessages);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="chat-layout">
      <div className="chat-panel">
        {!health?.has_api_key && (
          <div className="notice warning">
            <AlertTriangle size={18} />
            <span>后端没有检测到 OPENAI_API_KEY。启动服务前请先在终端 export API Key。</span>
          </div>
        )}

        <div className="chat-scroll" aria-live="polite">
          {messages.map((message, index) => (
            <MessageBubble message={message} key={`${message.role}-${index}`} />
          ))}
          {loading && (
            <article className="message assistant pending">
              <div className="message-meta">AI 医生</div>
              <p><Loader2 className="spin" size={16} /> 正在分析症状并检索病例库...</p>
            </article>
          )}
        </div>

        {error && <div className="notice error">{error}</div>}

        <form className="composer" onSubmit={submit}>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="例如：男，45岁，胸闷两天，活动后加重，伴出汗..."
            rows={3}
          />
          <div className="composer-actions">
            <button className="ghost-button" type="button" onClick={() => { setMessages(initialMessages); setReferences([]); }}>
              <RotateCcw size={17} />
              重置
            </button>
            <button className="primary-button" type="submit" disabled={!canSend}>
              <ArrowUp size={18} />
              发送
            </button>
          </div>
        </form>
      </div>

      <aside className="side-panel">
        <div className="panel-title">
          <Stethoscope size={18} />
          <h2>相似病例参考</h2>
        </div>
        <ReferenceList references={references} />
      </aside>
    </section>
  );
}
