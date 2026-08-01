import { useState } from "react";
import { App as AntApp, ConfigProvider, Layout, Menu, Select, Typography } from "antd";

import { DashboardPage } from "../features/dashboard/DashboardPage";
import { DataSourcePage } from "../features/datasource/DataSourcePage";
import { AiPromptPage } from "../features/insights/AiPromptPage";
import { TmfExportPage } from "../features/export/TmfExportPage";
import { TradeImportPage } from "../features/trades/TradeImportPage";
import { TradeListPage } from "../features/trades/TradeListPage";
import { I18nProvider, useI18n, type Language } from "./i18n";

const { Header, Content } = Layout;
type View = "dashboard" | "datasource" | "import" | "trades" | "prompt" | "export";

function Application() {
  const [view, setView] = useState<View>("dashboard");
  const { antdLocale, language, setLanguage, t } = useI18n();
  return <ConfigProvider locale={antdLocale} theme={{ token: { colorPrimary: "#1677ff", borderRadius: 8 } }}>
    <AntApp>
      <Layout style={{ minHeight: "100vh" }}>
        <Header style={{ display: "flex", alignItems: "center", gap: 40, background: "#001529" }}>
          <Typography.Title level={3} style={{ margin: 0, color: "white", whiteSpace: "nowrap" }}>TradeMirror</Typography.Title>
          <Menu theme="dark" mode="horizontal" selectedKeys={[view]} onClick={({ key }) => setView(key as View)} items={[
            { key: "dashboard", label: t("nav.dashboard") }, { key: "datasource", label: t("nav.datasource") }, { key: "prompt", label: t("nav.narrative") }, { key: "trades", label: t("nav.trades") }, { key: "import", label: t("nav.import") }, { key: "export", label: t("nav.export") },
          ]} style={{ flex: 1, minWidth: 0, background: "transparent" }} />
          <Select<Language> aria-label="Language" value={language} onChange={setLanguage} style={{ width: 112 }} options={[{ value: "zh-CN", label: t("language.zh") }, { value: "en-US", label: t("language.en") }]} />
        </Header>
        <Content style={{ padding: 32, maxWidth: 1280, width: "100%", margin: "0 auto" }}>
          {view === "dashboard" && <DashboardPage />}{view === "datasource" && <DataSourcePage />}{view === "import" && <TradeImportPage />}{view === "trades" && <TradeListPage />}{view === "prompt" && <AiPromptPage />}{view === "export" && <TmfExportPage />}
        </Content>
      </Layout>
    </AntApp>
  </ConfigProvider>;
}

export function App() {
  return <I18nProvider><Application /></I18nProvider>;
}
