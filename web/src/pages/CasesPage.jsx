import React from "react";
import { Activity, Database, FileText, Loader2, Play, RefreshCw, Search, Stethoscope } from "lucide-react";
import { getCases, getResults, getRun, startRun } from "../api";

function compactText(value, fallback = "暂无信息", maxLength = 96) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (!text) return fallback;
  return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;
}

function CaseList({ cases }) {
  if (!cases.length) {
    return <div className="empty-state">没有找到匹配病例。</div>;
  }

  return (
    <div className="case-list">
      {cases.map((item) => (
        <article className="case-row" key={item.id}>
          <div className="case-main">
            <div className="case-title-line">
              <span className="case-id">#{item.id}</span>
              <strong>{item.title || item.department || "未命名病例"}</strong>
            </div>
            <p>{compactText(item.chief_complaint || item.history, "暂无主诉", 118)}</p>
            <div className="case-tags">
              {item.department && <span>{item.department}</span>}
              {item.diseases && <span>{compactText(item.diseases, "", 42)}</span>}
            </div>
          </div>
          <div className="case-diagnosis">
            <small>诊断参考</small>
            <span>{compactText(item.diagnosis || item.diseases, "未标注", 76)}</span>
          </div>
        </article>
      ))}
    </div>
  );
}

function ResultList({ results }) {
  if (!results.length) {
    return <div className="empty-state">暂无运行结果。</div>;
  }

  return (
    <div className="result-list">
      {results.map((item) => (
        <article className="result-row" key={`${item.patient_id}-${item.time}`}>
          <div className="result-head">
            <strong>病例 #{item.patient_id}</strong>
            <span>{item.time}</span>
          </div>
          <p>{compactText(item.final, "暂无诊断摘要", 260)}</p>
        </article>
      ))}
    </div>
  );
}

export default function CasesPage() {
  const [query, setQuery] = React.useState("");
  const [cases, setCases] = React.useState([]);
  const [total, setTotal] = React.useState(0);
  const [results, setResults] = React.useState([]);
  const [limit, setLimit] = React.useState(1);
  const [job, setJob] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [caseData, resultData] = await Promise.all([getCases(query, 30), getResults(30)]);
      setCases(caseData.items || []);
      setTotal(caseData.total || 0);
      setResults(resultData.items || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [query]);

  React.useEffect(() => {
    refresh();
  }, [refresh]);

  React.useEffect(() => {
    if (!job || !["queued", "running"].includes(job.status)) return undefined;
    const timer = window.setInterval(async () => {
      const nextJob = await getRun(job.id);
      setJob(nextJob);
      if (!["queued", "running"].includes(nextJob.status)) {
        refresh();
      }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [job, refresh]);

  const runCases = async () => {
    setError("");
    try {
      const nextJob = await startRun(Number(limit));
      setJob(nextJob);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <section className="cases-layout">
      <div className="summary-grid">
        <article className="summary-card">
          <Database size={20} />
          <div>
            <span>病例总数</span>
            <strong>{total || "--"}</strong>
          </div>
        </article>
        <article className="summary-card">
          <FileText size={20} />
          <div>
            <span>诊断结果</span>
            <strong>{results.length}</strong>
          </div>
        </article>
        <article className="summary-card">
          <Activity size={20} />
          <div>
            <span>运行状态</span>
            <strong>{job?.status || "idle"}</strong>
          </div>
        </article>
      </div>

      <div className="toolbar case-toolbar">
        <label className="search-box">
          <Search size={18} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="搜索症状、疾病、科室，例如：胸闷、脑梗死、呼吸内科"
          />
        </label>
        <button className="ghost-button" type="button" onClick={refresh}>
          <RefreshCw size={17} />
          刷新
        </button>
      </div>

      {error && <div className="notice error">{error}</div>}

      <div className="cases-grid">
        <section className="data-panel">
          <div className="panel-title">
            <Stethoscope size={18} />
            <h2>病例库</h2>
            <span>显示 {cases.length} / {total} 条</span>
          </div>
          {loading ? <div className="empty-state"><Loader2 className="spin" size={18} /> 加载中...</div> : <CaseList cases={cases} />}
        </section>

        <section className="data-panel run-panel">
          <div className="panel-title">
            <Play size={18} />
            <h2>小批量运行</h2>
          </div>
          <p className="panel-help">适合先跑 1 到 5 条检查效果，避免一次消耗过多 API 额度。</p>
          <div className="run-box">
            <label>
              本次运行病例数
              <input
                type="number"
                min="1"
                max="606"
                value={limit}
                onChange={(event) => setLimit(event.target.value)}
              />
            </label>
            <button className="primary-button" type="button" onClick={runCases} disabled={job && ["queued", "running"].includes(job.status)}>
              <Play size={17} />
              开始运行
            </button>
          </div>
          {job && (
            <div className="job-box">
              <div className="job-line">
                <strong>任务 {job.id}</strong>
                <span className={`job-status ${job.status}`}>{job.status}</span>
              </div>
              {job.output && <pre>{job.output}</pre>}
            </div>
          )}
        </section>
      </div>

      <section className="data-panel results-panel">
        <div className="panel-title">
          <FileText size={18} />
          <h2>诊断结果</h2>
          <span>最近 {results.length} 条</span>
        </div>
        <ResultList results={results} />
      </section>
    </section>
  );
}
