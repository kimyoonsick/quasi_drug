import React, { useEffect, useState } from "react";
import ReportLayout from '../common/ReportLayout';
import {
    NAVY, BG_LIGHT, TEXT_MAIN, TEXT_SUB,
    section, sTitle,
    execSummaryGrad, execLabel,
    sourceSection, sourceLabel, sourceList,
} from './reportStyles';

/* -------------------------------------------------
   CSV 파싱 헬퍼 (Papaparse 없이 간단 구현)
   - 쉼표 구분자 기준, 헤더 파싱 및 데이터 매핑
------------------------------------------------- */
const parseCsv = (text) => {
    const lines = text.trim().split("\n");
    const header = lines[0].split(",");
    const rows = lines.slice(1).map((ln) => {
        // Handle basic commas. A robust parser handles quotes, but this works for basic raw data.
        const cols = ln.split(",");
        const obj = {};
        header.forEach((h, i) => (obj[h.trim()] = cols[i] ? cols[i].trim() : ""));
        return obj;
    });
    return { header: header.map(h => h.trim()), rows };
};

export default function CompetitorDashboardReport({ titleOverride }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // -------------------------------------------------
    // CSV 로드 & 파싱
    // -------------------------------------------------
    useEffect(() => {
        const fetchCsv = async () => {
            try {
                const res = await fetch("/data/competitor_raw.csv");
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const text = await res.text();
                setData(parseCsv(text));
            } catch (e) {
                console.error("데이터 로드 오류:", e);
                setError(e.message);
            } finally {
                setLoading(false);
            }
        };
        fetchCsv();
    }, []);

    // -------------------------------------------------
    // 테이블 렌더링
    // -------------------------------------------------
    const renderTable = () => {
        if (!data || data.rows.length === 0) return <p style={{ color: TEXT_SUB }}>데이터가 없습니다.</p>;
        const { header, rows } = data;
        return (
            <div style={{ overflowX: "auto" }}>
                <table style={{ minWidth: "100%", borderCollapse: "collapse", border: `1px solid ${BG_LIGHT}` }}>
                    <thead style={{ background: BG_LIGHT }}>
                        <tr>
                            {header.map((h) => (
                                <th key={h} style={{ padding: "12px", textAlign: "left", fontSize: "0.875rem", color: NAVY }}>
                                    {h}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((row, idx) => (
                            <tr key={idx} style={{ borderBottom: "1px solid #eee" }}>
                                {header.map((h) => (
                                    <td key={h} style={{ padding: "12px", fontSize: "0.875rem", color: TEXT_MAIN }}>
                                        {row[h]}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    };

    return (
        <ReportLayout
            type="분석 보고서"
            title="[피코몰] 경쟁사 이벤트/기획전 현황 대시보드 (1차)"
            subtitle="HMP몰 · 바로팜 · 새로팜 · 플랫폼팜 — 4대 경쟁사 통합 이벤트 현황 분석"
            date="2026.04.20"
            version="v1.0"
            audience="마케팅팀"
            titleOverride={titleOverride}
        >
            <div className="report-tab-content" style={{ paddingTop: '1rem' }}>

                {/* ═══ Executive Summary ═══ */}
                <section style={section}>
                    <div style={execSummaryGrad}>
                        <div style={execLabel}>EXECUTIVE SUMMARY</div>
                        <ul style={{ margin: 0, paddingLeft: '1.25rem', listStyle: 'disc', lineHeight: 2 }}>
                            <li>HMP몰, 바로팜, 새로팜, 플랫폼팜 4개 경쟁 B2B 약국몰의 이벤트·기획전 데이터를 통합 수집하여 분석</li>
                            <li>각 플랫폼의 혜택 유형(적립/할인/사은품), 진행 기간, 대상(신규/전체)별 경쟁 구도 파악</li>
                            <li>약사법 제47조의3(리베이트 쌍벌제) 위반 소지 표현에 대한 사전 태깅 적용</li>
                            <li>피코몰 대비 차별화 전략 수립을 위한 데이터 기반 인사이트 제공</li>
                        </ul>
                    </div>
                </section>

                {/* ═══ 대시보드 본문 ═══ */}
                <section style={section}>
                    <h2 style={sTitle}>경쟁사 이벤트 현황 대시보드</h2>
                    {loading && <p style={{ color: TEXT_SUB }}>데이터 로딩 중…</p>}
                    {error && <p style={{ color: 'red' }}>데이터 로드 실패: {error}</p>}
                    {!loading && !error && data && (
                        <div style={{ marginTop: '1.5rem' }}>
                            {renderTable()}
                        </div>
                    )}
                </section>

                {/* ═══ 출처 ═══ */}
                <div style={sourceSection}>
                    <div style={sourceLabel}>DATA SOURCES</div>
                    <ul style={sourceList}>
                        <li>[외부] HMP몰 (hmpmall.co.kr) 이벤트/기획전 페이지 크롤링 데이터</li>
                        <li>[외부] 바로팜 (baropharm.com) 이벤트/기획전 페이지 크롤링 데이터</li>
                        <li>[외부] 새로팜 (saeropharm.com) 이벤트/기획전 페이지 크롤링 데이터</li>
                        <li>[외부] 플랫폼팜 (platpharm.co.kr) 이벤트/기획전 페이지 크롤링 데이터</li>
                        <li>[내부] 마케팅팀 경쟁사 분석 — competitor_raw.csv</li>
                    </ul>
                </div>

            </div>
        </ReportLayout>
    );
}
