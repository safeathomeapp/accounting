--
-- PostgreSQL database dump
--

\restrict GXbsElkyvGAhxZymDGcKsTWqxKPPR6ecKLgwnMn7VESnJZxrMUAAoOsAY3FHpb9

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

-- Started on 2026-01-22 23:53:53

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 910 (class 1247 OID 49956)
-- Name: forecastmethod; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.forecastmethod AS ENUM (
    'LINEAR_REGRESSION',
    'MOVING_AVERAGE',
    'EXPONENTIAL_SMOOTHING',
    'SEASONAL_DECOMPOSITION',
    'MANUAL'
);


ALTER TYPE public.forecastmethod OWNER TO postgres;

--
-- TOC entry 907 (class 1247 OID 49944)
-- Name: forecasttype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.forecasttype AS ENUM (
    'REVENUE',
    'EXPENSE',
    'CASH_FLOW',
    'PROFIT',
    'ACCOUNT_BALANCE'
);


ALTER TYPE public.forecasttype OWNER TO postgres;

--
-- TOC entry 913 (class 1247 OID 49968)
-- Name: metrictype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.metrictype AS ENUM (
    'GROSS_PROFIT_MARGIN',
    'NET_PROFIT_MARGIN',
    'RETURN_ON_ASSETS',
    'RETURN_ON_EQUITY',
    'CURRENT_RATIO',
    'QUICK_RATIO',
    'DEBT_TO_EQUITY',
    'ASSET_TURNOVER',
    'REVENUE_GROWTH',
    'EXPENSE_RATIO'
);


ALTER TYPE public.metrictype OWNER TO postgres;

--
-- TOC entry 961 (class 1247 OID 50128)
-- Name: reportformat; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.reportformat AS ENUM (
    'PDF',
    'EXCEL',
    'JSON'
);


ALTER TYPE public.reportformat OWNER TO postgres;

--
-- TOC entry 958 (class 1247 OID 50115)
-- Name: reportfrequency; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.reportfrequency AS ENUM (
    'DAILY',
    'WEEKLY',
    'MONTHLY',
    'QUARTERLY',
    'ANNUAL',
    'ONCE'
);


ALTER TYPE public.reportfrequency OWNER TO postgres;

--
-- TOC entry 916 (class 1247 OID 49990)
-- Name: trenddirection; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.trenddirection AS ENUM (
    'UPWARD',
    'DOWNWARD',
    'STABLE'
);


ALTER TYPE public.trenddirection OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 219 (class 1259 OID 49779)
-- Name: accounting_platforms; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.accounting_platforms (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    platform_name character varying(50) NOT NULL,
    platform_version character varying(50),
    client_id character varying(500) NOT NULL,
    client_secret_encrypted bytea NOT NULL,
    access_token_encrypted bytea,
    refresh_token_encrypted bytea,
    token_expires_at timestamp with time zone,
    tenant_id character varying(255),
    realm_id character varying(255),
    is_active boolean NOT NULL,
    connection_status character varying(50) NOT NULL,
    last_sync_at timestamp with time zone,
    last_error_message character varying(500),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.accounting_platforms OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 49798)
-- Name: accounts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.accounts (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    platform_id character varying(500) NOT NULL,
    platform_name character varying(50) NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(255) NOT NULL,
    account_type character varying(50),
    description character varying(500),
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.accounts OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 49849)
-- Name: ai_analysis_results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ai_analysis_results (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    suggested_account_id uuid,
    analysis_type character varying(50) NOT NULL,
    target_entity_type character varying(50),
    target_entity_id uuid,
    prompt_used text NOT NULL,
    prompt_tokens integer,
    response_tokens integer,
    result_text text NOT NULL,
    result_json jsonb,
    confidence_score numeric(3,2),
    suggested_category character varying(100),
    suggested_account_id_local uuid,
    is_approved boolean NOT NULL,
    was_used boolean NOT NULL,
    estimated_cost_gbp numeric(7,4),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.ai_analysis_results OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 49763)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 49815)
-- Name: audit_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_log (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    table_name character varying(100) NOT NULL,
    record_id character varying(500) NOT NULL,
    operation character varying(10) NOT NULL,
    old_values jsonb,
    new_values jsonb,
    changed_by character varying(100) NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.audit_log OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 49830)
-- Name: clients; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.clients (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    platform_id character varying(500) NOT NULL,
    platform_name character varying(50) NOT NULL,
    name character varying(255) NOT NULL,
    email character varying(255),
    phone character varying(20),
    website character varying(255),
    address_line1 character varying(255),
    address_line2 character varying(255),
    city character varying(100),
    postal_code character varying(20),
    country character varying(100),
    contact_type character varying(50),
    industry character varying(100),
    tax_number character varying(50),
    is_active boolean NOT NULL,
    last_synced_at timestamp with time zone,
    platform_updated_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.clients OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 50011)
-- Name: conversion_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.conversion_history (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    source_amount double precision NOT NULL,
    source_currency_code character varying(3) NOT NULL,
    target_amount double precision NOT NULL,
    target_currency_code character varying(3) NOT NULL,
    exchange_rate double precision NOT NULL,
    conversion_date timestamp with time zone NOT NULL,
    conversion_method character varying(20) NOT NULL,
    transaction_id uuid,
    converted_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.conversion_history OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 49997)
-- Name: currencies; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.currencies (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    code character varying(3) NOT NULL,
    name character varying(100) NOT NULL,
    symbol character varying(10) NOT NULL,
    decimal_places integer NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.currencies OWNER TO postgres;

--
-- TOC entry 238 (class 1259 OID 50091)
-- Name: dashboard_widgets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dashboard_widgets (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    title character varying(200) NOT NULL,
    widget_type character varying(50) NOT NULL,
    "position" integer,
    size character varying(20),
    data_source character varying(100) NOT NULL,
    metric_types character varying(500),
    period_range character varying(50),
    config text,
    is_active boolean,
    is_pinned boolean,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.dashboard_widgets OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 50004)
-- Name: exchange_rates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.exchange_rates (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    source_currency_code character varying(3) NOT NULL,
    target_currency_code character varying(3) NOT NULL,
    rate double precision NOT NULL,
    effective_date timestamp with time zone NOT NULL,
    source character varying(20) NOT NULL,
    provider character varying(100),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.exchange_rates OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 50062)
-- Name: financial_metrics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.financial_metrics (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    metric_type public.metrictype NOT NULL,
    period_date date NOT NULL,
    metric_value numeric(15,4) NOT NULL,
    previous_period_value numeric(15,4),
    period_over_period_change numeric(15,4),
    benchmark_value numeric(15,4),
    vs_benchmark numeric(15,4),
    calculation_notes text,
    is_active boolean,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.financial_metrics OWNER TO postgres;

--
-- TOC entry 235 (class 1259 OID 50053)
-- Name: forecasts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.forecasts (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    forecast_type public.forecasttype NOT NULL,
    method public.forecastmethod NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    forecast_date date NOT NULL,
    base_value numeric(15,2) NOT NULL,
    forecasted_value numeric(15,2) NOT NULL,
    lower_bound numeric(15,2),
    upper_bound numeric(15,2),
    confidence_level double precision,
    accuracy_score double precision,
    mape double precision,
    reference_account_id uuid,
    reference_category character varying(100),
    notes text,
    is_active boolean,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.forecasts OWNER TO postgres;

--
-- TOC entry 239 (class 1259 OID 50101)
-- Name: kpis; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.kpis (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    name character varying(200) NOT NULL,
    code character varying(50) NOT NULL,
    description text,
    period_date date NOT NULL,
    current_value numeric(15,4) NOT NULL,
    target_value numeric(15,4),
    status_vs_target double precision,
    trend public.trenddirection,
    period_over_period_change numeric(15,4),
    unit character varying(50),
    formula text,
    is_active boolean,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.kpis OWNER TO postgres;

--
-- TOC entry 244 (class 1259 OID 50176)
-- Name: mobile_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mobile_sessions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    organization_id uuid NOT NULL,
    device_id character varying(255) NOT NULL,
    device_name character varying(255),
    device_os character varying(50),
    app_version character varying(50),
    access_token text NOT NULL,
    access_token_expires_at timestamp with time zone NOT NULL,
    refresh_token text NOT NULL,
    refresh_token_expires_at timestamp with time zone NOT NULL,
    login_at timestamp with time zone NOT NULL,
    last_activity_at timestamp with time zone NOT NULL,
    logout_at timestamp with time zone,
    is_active integer,
    revocation_reason character varying(100),
    last_error text,
    refresh_count integer,
    request_count integer
);


ALTER TABLE public.mobile_sessions OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 49875)
-- Name: oauth_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.oauth_tokens (
    id uuid NOT NULL,
    platform_id uuid NOT NULL,
    access_token_encrypted bytea NOT NULL,
    refresh_token_encrypted bytea,
    token_type character varying(50) NOT NULL,
    issued_at timestamp with time zone NOT NULL,
    expires_at timestamp with time zone,
    scopes text,
    is_revoked boolean NOT NULL,
    revoked_at timestamp with time zone,
    revoke_reason character varying(255),
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.oauth_tokens OWNER TO postgres;

--
-- TOC entry 245 (class 1259 OID 50185)
-- Name: offline_sync_queue; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.offline_sync_queue (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    user_id uuid NOT NULL,
    action character varying(50) NOT NULL,
    entity_type character varying(50) NOT NULL,
    entity_data json NOT NULL,
    status character varying(50) NOT NULL,
    attempt_count integer,
    next_retry_at timestamp with time zone,
    last_error text,
    created_at timestamp with time zone NOT NULL,
    first_sync_attempt_at timestamp with time zone,
    last_sync_attempt_at timestamp with time zone,
    synced_at timestamp with time zone,
    server_entity_id uuid,
    notes text
);


ALTER TABLE public.offline_sync_queue OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 49768)
-- Name: organizations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.organizations (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    phone character varying(20),
    address_line1 character varying(255),
    address_line2 character varying(255),
    city character varying(100),
    postal_code character varying(20),
    country character varying(100) NOT NULL,
    timezone character varying(50) NOT NULL,
    currency character varying(3) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.organizations OWNER TO postgres;

--
-- TOC entry 246 (class 1259 OID 50197)
-- Name: push_device_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.push_device_tokens (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    organization_id uuid NOT NULL,
    device_id character varying(255) NOT NULL,
    device_name character varying(255),
    token text NOT NULL,
    token_type character varying(50),
    is_active boolean,
    registered_at timestamp with time zone NOT NULL,
    last_used_at timestamp with time zone,
    invalidated_at timestamp with time zone,
    invalidation_reason character varying(100),
    failed_attempts integer
);


ALTER TABLE public.push_device_tokens OWNER TO postgres;

--
-- TOC entry 247 (class 1259 OID 50207)
-- Name: push_notification_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.push_notification_logs (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    organization_id uuid NOT NULL,
    device_token_id uuid NOT NULL,
    notification_type character varying(50) NOT NULL,
    title character varying(200) NOT NULL,
    body character varying(500) NOT NULL,
    data character varying(1000),
    status character varying(50) NOT NULL,
    sent_at timestamp with time zone,
    failure_reason text,
    opened_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.push_notification_logs OWNER TO postgres;

--
-- TOC entry 248 (class 1259 OID 50219)
-- Name: push_notification_preferences; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.push_notification_preferences (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    organization_id uuid NOT NULL,
    sync_notifications_enabled boolean,
    alert_notifications_enabled boolean,
    info_notifications_enabled boolean,
    report_notifications_enabled boolean,
    quiet_hours_start character varying(5),
    quiet_hours_end character varying(5),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone
);


ALTER TABLE public.push_notification_preferences OWNER TO postgres;

--
-- TOC entry 243 (class 1259 OID 50165)
-- Name: report_distributions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.report_distributions (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    report_id uuid NOT NULL,
    schedule_id uuid,
    recipient_email character varying(200) NOT NULL,
    status character varying(20),
    error_message text,
    sent_at timestamp without time zone,
    opened_at timestamp without time zone,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.report_distributions OWNER TO postgres;

--
-- TOC entry 241 (class 1259 OID 50144)
-- Name: report_schedules; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.report_schedules (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    template_id uuid NOT NULL,
    name character varying(200) NOT NULL,
    frequency public.reportfrequency NOT NULL,
    format public.reportformat NOT NULL,
    start_date date NOT NULL,
    end_date date,
    day_of_week integer,
    day_of_month integer,
    hour_utc integer,
    recipient_emails character varying(1000) NOT NULL,
    include_body_text boolean,
    subject_template character varying(200),
    is_active boolean,
    last_run timestamp without time zone,
    next_run timestamp without time zone NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.report_schedules OWNER TO postgres;

--
-- TOC entry 240 (class 1259 OID 50135)
-- Name: report_templates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.report_templates (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    template_type character varying(50) NOT NULL,
    include_sections character varying(500),
    date_range_days integer,
    compare_previous boolean,
    include_charts boolean,
    include_summary boolean,
    company_name_override character varying(200),
    logo_url character varying(500),
    footer_text text,
    is_active boolean,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.report_templates OWNER TO postgres;

--
-- TOC entry 242 (class 1259 OID 50155)
-- Name: reports; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reports (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    schedule_id uuid,
    template_id uuid NOT NULL,
    report_type character varying(50) NOT NULL,
    format public.reportformat NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    file_size integer,
    file_key character varying(500),
    file_url character varying(500),
    title character varying(200),
    summary text,
    data_points_count integer,
    status character varying(20),
    generated_at timestamp without time zone NOT NULL,
    expires_at timestamp without time zone,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.reports OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 49891)
-- Name: sync_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sync_history (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    platform_id uuid,
    sync_type character varying(50) NOT NULL,
    sync_status character varying(50) NOT NULL,
    records_synced integer NOT NULL,
    records_created integer NOT NULL,
    records_updated integer NOT NULL,
    records_failed integer NOT NULL,
    started_at timestamp with time zone NOT NULL,
    completed_at timestamp with time zone,
    duration_seconds integer,
    error_message text,
    error_details jsonb,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.sync_history OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 50039)
-- Name: tax_adjustments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tax_adjustments (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    tax_liability_id uuid NOT NULL,
    adjustment_type character varying(20) NOT NULL,
    amount numeric(12,2) NOT NULL,
    reason character varying(255) NOT NULL,
    description text,
    applied_date date NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.tax_adjustments OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 50046)
-- Name: tax_compliance_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tax_compliance_logs (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    event_type character varying(50) NOT NULL,
    description text NOT NULL,
    affected_entity_id uuid,
    affected_entity_type character varying(50),
    event_metadata json,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.tax_compliance_logs OWNER TO postgres;

--
-- TOC entry 232 (class 1259 OID 50032)
-- Name: tax_liabilities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tax_liabilities (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    tax_type_id uuid NOT NULL,
    tax_year integer NOT NULL,
    period character varying(10) NOT NULL,
    calculated_amount numeric(12,2) NOT NULL,
    paid_amount numeric(12,2) NOT NULL,
    balance numeric(12,2) NOT NULL,
    due_date date NOT NULL,
    status character varying(20) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.tax_liabilities OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 50025)
-- Name: tax_rates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tax_rates (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    tax_type_id uuid NOT NULL,
    jurisdiction character varying(100) NOT NULL,
    rate numeric(5,4) NOT NULL,
    effective_date date NOT NULL,
    expiration_date date,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.tax_rates OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 50016)
-- Name: tax_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tax_types (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    tax_type_category character varying(30) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.tax_types OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 49912)
-- Name: transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transactions (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    client_id uuid,
    account_id uuid,
    platform_id character varying(500) NOT NULL,
    platform_name character varying(50) NOT NULL,
    transaction_type character varying(50) NOT NULL,
    reference_number character varying(100),
    description text,
    amount numeric(15,2) NOT NULL,
    tax_amount numeric(15,2) NOT NULL,
    total_amount numeric(15,2) NOT NULL,
    currency character varying(3) NOT NULL,
    transaction_date date NOT NULL,
    due_date date,
    status character varying(50),
    is_reconciled boolean NOT NULL,
    last_synced_at timestamp with time zone,
    platform_updated_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.transactions OWNER TO postgres;

--
-- TOC entry 237 (class 1259 OID 50071)
-- Name: trend_analysis; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.trend_analysis (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    metric_type character varying(100) NOT NULL,
    category character varying(100),
    analysis_period_start date NOT NULL,
    analysis_period_end date NOT NULL,
    trend_direction public.trenddirection NOT NULL,
    strength double precision,
    average_value numeric(15,2),
    min_value numeric(15,2),
    max_value numeric(15,2),
    growth_rate numeric(15,4),
    volatility double precision,
    seasonal_pattern text,
    anomalies_detected integer,
    notes text,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.trend_analysis OWNER TO postgres;

--
-- TOC entry 4845 (class 2606 OID 49785)
-- Name: accounting_platforms accounting_platforms_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounting_platforms
    ADD CONSTRAINT accounting_platforms_pkey PRIMARY KEY (id);


--
-- TOC entry 4854 (class 2606 OID 49804)
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (id);


--
-- TOC entry 4875 (class 2606 OID 49855)
-- Name: ai_analysis_results ai_analysis_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ai_analysis_results
    ADD CONSTRAINT ai_analysis_results_pkey PRIMARY KEY (id);


--
-- TOC entry 4837 (class 2606 OID 49767)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 4861 (class 2606 OID 49821)
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- TOC entry 4866 (class 2606 OID 49836)
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id);


--
-- TOC entry 4912 (class 2606 OID 50015)
-- Name: conversion_history conversion_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.conversion_history
    ADD CONSTRAINT conversion_history_pkey PRIMARY KEY (id);


--
-- TOC entry 4904 (class 2606 OID 50001)
-- Name: currencies currencies_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.currencies
    ADD CONSTRAINT currencies_pkey PRIMARY KEY (id);


--
-- TOC entry 4941 (class 2606 OID 50097)
-- Name: dashboard_widgets dashboard_widgets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dashboard_widgets
    ADD CONSTRAINT dashboard_widgets_pkey PRIMARY KEY (id);


--
-- TOC entry 4908 (class 2606 OID 50008)
-- Name: exchange_rates exchange_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exchange_rates
    ADD CONSTRAINT exchange_rates_pkey PRIMARY KEY (id);


--
-- TOC entry 4934 (class 2606 OID 50068)
-- Name: financial_metrics financial_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.financial_metrics
    ADD CONSTRAINT financial_metrics_pkey PRIMARY KEY (id);


--
-- TOC entry 4930 (class 2606 OID 50059)
-- Name: forecasts forecasts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.forecasts
    ADD CONSTRAINT forecasts_pkey PRIMARY KEY (id);


--
-- TOC entry 4948 (class 2606 OID 50109)
-- Name: kpis kpis_org_code_date_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.kpis
    ADD CONSTRAINT kpis_org_code_date_unique UNIQUE (organization_id, code, period_date);


--
-- TOC entry 4950 (class 2606 OID 50107)
-- Name: kpis kpis_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.kpis
    ADD CONSTRAINT kpis_pkey PRIMARY KEY (id);


--
-- TOC entry 4974 (class 2606 OID 50182)
-- Name: mobile_sessions mobile_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mobile_sessions
    ADD CONSTRAINT mobile_sessions_pkey PRIMARY KEY (id);


--
-- TOC entry 4885 (class 2606 OID 49881)
-- Name: oauth_tokens oauth_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.oauth_tokens
    ADD CONSTRAINT oauth_tokens_pkey PRIMARY KEY (id);


--
-- TOC entry 4981 (class 2606 OID 50191)
-- Name: offline_sync_queue offline_sync_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.offline_sync_queue
    ADD CONSTRAINT offline_sync_queue_pkey PRIMARY KEY (id);


--
-- TOC entry 4843 (class 2606 OID 49774)
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- TOC entry 4986 (class 2606 OID 50203)
-- Name: push_device_tokens push_device_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.push_device_tokens
    ADD CONSTRAINT push_device_tokens_pkey PRIMARY KEY (id);


--
-- TOC entry 4993 (class 2606 OID 50213)
-- Name: push_notification_logs push_notification_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.push_notification_logs
    ADD CONSTRAINT push_notification_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 4997 (class 2606 OID 50223)
-- Name: push_notification_preferences push_notification_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.push_notification_preferences
    ADD CONSTRAINT push_notification_preferences_pkey PRIMARY KEY (id);


--
-- TOC entry 4970 (class 2606 OID 50171)
-- Name: report_distributions report_distributions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.report_distributions
    ADD CONSTRAINT report_distributions_pkey PRIMARY KEY (id);


--
-- TOC entry 4960 (class 2606 OID 50150)
-- Name: report_schedules report_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.report_schedules
    ADD CONSTRAINT report_schedules_pkey PRIMARY KEY (id);


--
-- TOC entry 4954 (class 2606 OID 50141)
-- Name: report_templates report_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.report_templates
    ADD CONSTRAINT report_templates_pkey PRIMARY KEY (id);


--
-- TOC entry 4965 (class 2606 OID 50161)
-- Name: reports reports_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_pkey PRIMARY KEY (id);


--
-- TOC entry 4891 (class 2606 OID 49897)
-- Name: sync_history sync_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sync_history
    ADD CONSTRAINT sync_history_pkey PRIMARY KEY (id);


--
-- TOC entry 4926 (class 2606 OID 50045)
-- Name: tax_adjustments tax_adjustments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_adjustments
    ADD CONSTRAINT tax_adjustments_pkey PRIMARY KEY (id);


--
-- TOC entry 4928 (class 2606 OID 50052)
-- Name: tax_compliance_logs tax_compliance_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_compliance_logs
    ADD CONSTRAINT tax_compliance_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 4922 (class 2606 OID 50036)
-- Name: tax_liabilities tax_liabilities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_liabilities
    ADD CONSTRAINT tax_liabilities_pkey PRIMARY KEY (id);


--
-- TOC entry 4918 (class 2606 OID 50029)
-- Name: tax_rates tax_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_rates
    ADD CONSTRAINT tax_rates_pkey PRIMARY KEY (id);


--
-- TOC entry 4914 (class 2606 OID 50022)
-- Name: tax_types tax_types_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_types
    ADD CONSTRAINT tax_types_pkey PRIMARY KEY (id);


--
-- TOC entry 4902 (class 2606 OID 49918)
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- TOC entry 4939 (class 2606 OID 50077)
-- Name: trend_analysis trend_analysis_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.trend_analysis
    ADD CONSTRAINT trend_analysis_pkey PRIMARY KEY (id);


--
-- TOC entry 4906 (class 2606 OID 50003)
-- Name: currencies uq_currency_org_code; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.currencies
    ADD CONSTRAINT uq_currency_org_code UNIQUE (organization_id, code);


--
-- TOC entry 4910 (class 2606 OID 50010)
-- Name: exchange_rates uq_exchange_rate_org_pair_date_source; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exchange_rates
    ADD CONSTRAINT uq_exchange_rate_org_pair_date_source UNIQUE (organization_id, source_currency_code, target_currency_code, effective_date, source);


--
-- TOC entry 4924 (class 2606 OID 50038)
-- Name: tax_liabilities uq_tax_liability_org_type_year_period; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_liabilities
    ADD CONSTRAINT uq_tax_liability_org_type_year_period UNIQUE (organization_id, tax_type_id, tax_year, period);


--
-- TOC entry 4920 (class 2606 OID 50031)
-- Name: tax_rates uq_tax_rate_org_type_juris_date; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_rates
    ADD CONSTRAINT uq_tax_rate_org_type_juris_date UNIQUE (organization_id, tax_type_id, jurisdiction, effective_date);


--
-- TOC entry 4916 (class 2606 OID 50024)
-- Name: tax_types uq_tax_type_org_code; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_types
    ADD CONSTRAINT uq_tax_type_org_code UNIQUE (organization_id, code);


--
-- TOC entry 4846 (class 1259 OID 49791)
-- Name: ix_accounting_platforms_connection_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_accounting_platforms_connection_status ON public.accounting_platforms USING btree (connection_status);


--
-- TOC entry 4847 (class 1259 OID 49792)
-- Name: ix_accounting_platforms_is_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_accounting_platforms_is_active ON public.accounting_platforms USING btree (is_active);


--
-- TOC entry 4848 (class 1259 OID 49793)
-- Name: ix_accounting_platforms_last_sync_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_accounting_platforms_last_sync_at ON public.accounting_platforms USING btree (last_sync_at);


--
-- TOC entry 4849 (class 1259 OID 49794)
-- Name: ix_accounting_platforms_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_accounting_platforms_organization_id ON public.accounting_platforms USING btree (organization_id);


--
-- TOC entry 4850 (class 1259 OID 49795)
-- Name: ix_accounting_platforms_platform_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_accounting_platforms_platform_name ON public.accounting_platforms USING btree (platform_name);


--
-- TOC entry 4851 (class 1259 OID 49796)
-- Name: ix_accounting_platforms_realm_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_accounting_platforms_realm_id ON public.accounting_platforms USING btree (realm_id);


--
-- TOC entry 4852 (class 1259 OID 49797)
-- Name: ix_accounting_platforms_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_accounting_platforms_tenant_id ON public.accounting_platforms USING btree (tenant_id);


--
-- TOC entry 4855 (class 1259 OID 49810)
-- Name: ix_accounts_account_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_accounts_account_type ON public.accounts USING btree (account_type);


--
-- TOC entry 4856 (class 1259 OID 49811)
-- Name: ix_accounts_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_accounts_name ON public.accounts USING btree (name);


--
-- TOC entry 4857 (class 1259 OID 49812)
-- Name: ix_accounts_org_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_accounts_org_code ON public.accounts USING btree (organization_id, code);


--
-- TOC entry 4858 (class 1259 OID 49813)
-- Name: ix_accounts_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_accounts_organization_id ON public.accounts USING btree (organization_id);


--
-- TOC entry 4859 (class 1259 OID 49814)
-- Name: ix_accounts_platform_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_accounts_platform_name ON public.accounts USING btree (platform_name);


--
-- TOC entry 4876 (class 1259 OID 49871)
-- Name: ix_ai_analysis_results_analysis_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ai_analysis_results_analysis_type ON public.ai_analysis_results USING btree (analysis_type);


--
-- TOC entry 4877 (class 1259 OID 49872)
-- Name: ix_ai_analysis_results_is_approved; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ai_analysis_results_is_approved ON public.ai_analysis_results USING btree (is_approved);


--
-- TOC entry 4878 (class 1259 OID 49873)
-- Name: ix_ai_analysis_results_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ai_analysis_results_organization_id ON public.ai_analysis_results USING btree (organization_id);


--
-- TOC entry 4879 (class 1259 OID 49874)
-- Name: ix_ai_analysis_results_target_entity_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_ai_analysis_results_target_entity_id ON public.ai_analysis_results USING btree (target_entity_id);


--
-- TOC entry 4862 (class 1259 OID 49827)
-- Name: ix_audit_log_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_log_created_at ON public.audit_log USING btree (created_at);


--
-- TOC entry 4863 (class 1259 OID 49828)
-- Name: ix_audit_log_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_log_organization_id ON public.audit_log USING btree (organization_id);


--
-- TOC entry 4864 (class 1259 OID 49829)
-- Name: ix_audit_log_table_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_audit_log_table_name ON public.audit_log USING btree (table_name);


--
-- TOC entry 4867 (class 1259 OID 49842)
-- Name: ix_clients_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_clients_email ON public.clients USING btree (email);


--
-- TOC entry 4868 (class 1259 OID 49843)
-- Name: ix_clients_is_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_clients_is_active ON public.clients USING btree (is_active);


--
-- TOC entry 4869 (class 1259 OID 49844)
-- Name: ix_clients_last_synced_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_clients_last_synced_at ON public.clients USING btree (last_synced_at);


--
-- TOC entry 4870 (class 1259 OID 49845)
-- Name: ix_clients_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_clients_name ON public.clients USING btree (name);


--
-- TOC entry 4871 (class 1259 OID 49846)
-- Name: ix_clients_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_clients_organization_id ON public.clients USING btree (organization_id);


--
-- TOC entry 4872 (class 1259 OID 49847)
-- Name: ix_clients_platform_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_clients_platform_name ON public.clients USING btree (platform_name);


--
-- TOC entry 4873 (class 1259 OID 49848)
-- Name: ix_clients_platform_reference; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_clients_platform_reference ON public.clients USING btree (platform_name, platform_id);


--
-- TOC entry 4942 (class 1259 OID 50098)
-- Name: ix_dashboard_widgets_is_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_dashboard_widgets_is_active ON public.dashboard_widgets USING btree (is_active);


--
-- TOC entry 4943 (class 1259 OID 50099)
-- Name: ix_dashboard_widgets_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_dashboard_widgets_organization_id ON public.dashboard_widgets USING btree (organization_id);


--
-- TOC entry 4935 (class 1259 OID 50069)
-- Name: ix_financial_metrics_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_financial_metrics_organization_id ON public.financial_metrics USING btree (organization_id);


--
-- TOC entry 4936 (class 1259 OID 50070)
-- Name: ix_financial_metrics_period_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_financial_metrics_period_date ON public.financial_metrics USING btree (period_date);


--
-- TOC entry 4931 (class 1259 OID 50061)
-- Name: ix_forecasts_is_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_forecasts_is_active ON public.forecasts USING btree (is_active);


--
-- TOC entry 4932 (class 1259 OID 50060)
-- Name: ix_forecasts_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_forecasts_organization_id ON public.forecasts USING btree (organization_id);


--
-- TOC entry 4944 (class 1259 OID 50111)
-- Name: ix_kpis_is_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_kpis_is_active ON public.kpis USING btree (is_active);


--
-- TOC entry 4945 (class 1259 OID 50112)
-- Name: ix_kpis_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_kpis_organization_id ON public.kpis USING btree (organization_id);


--
-- TOC entry 4946 (class 1259 OID 50110)
-- Name: ix_kpis_period_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_kpis_period_date ON public.kpis USING btree (period_date);


--
-- TOC entry 4971 (class 1259 OID 50184)
-- Name: ix_mobile_sessions_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_mobile_sessions_organization_id ON public.mobile_sessions USING btree (organization_id);


--
-- TOC entry 4972 (class 1259 OID 50183)
-- Name: ix_mobile_sessions_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_mobile_sessions_user_id ON public.mobile_sessions USING btree (user_id);


--
-- TOC entry 4880 (class 1259 OID 49887)
-- Name: ix_oauth_tokens_expires_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_oauth_tokens_expires_at ON public.oauth_tokens USING btree (expires_at);


--
-- TOC entry 4881 (class 1259 OID 49888)
-- Name: ix_oauth_tokens_is_revoked; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_oauth_tokens_is_revoked ON public.oauth_tokens USING btree (is_revoked);


--
-- TOC entry 4882 (class 1259 OID 49889)
-- Name: ix_oauth_tokens_issued_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_oauth_tokens_issued_at ON public.oauth_tokens USING btree (issued_at);


--
-- TOC entry 4883 (class 1259 OID 49890)
-- Name: ix_oauth_tokens_platform_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_oauth_tokens_platform_id ON public.oauth_tokens USING btree (platform_id);


--
-- TOC entry 4975 (class 1259 OID 50196)
-- Name: ix_offline_sync_queue_action; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_offline_sync_queue_action ON public.offline_sync_queue USING btree (action);


--
-- TOC entry 4976 (class 1259 OID 50195)
-- Name: ix_offline_sync_queue_entity_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_offline_sync_queue_entity_type ON public.offline_sync_queue USING btree (entity_type);


--
-- TOC entry 4977 (class 1259 OID 50192)
-- Name: ix_offline_sync_queue_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_offline_sync_queue_organization_id ON public.offline_sync_queue USING btree (organization_id);


--
-- TOC entry 4978 (class 1259 OID 50193)
-- Name: ix_offline_sync_queue_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_offline_sync_queue_status ON public.offline_sync_queue USING btree (status);


--
-- TOC entry 4979 (class 1259 OID 50194)
-- Name: ix_offline_sync_queue_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_offline_sync_queue_user_id ON public.offline_sync_queue USING btree (user_id);


--
-- TOC entry 4838 (class 1259 OID 49775)
-- Name: ix_organizations_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_organizations_created_at ON public.organizations USING btree (created_at);


--
-- TOC entry 4839 (class 1259 OID 49776)
-- Name: ix_organizations_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_organizations_email ON public.organizations USING btree (email);


--
-- TOC entry 4840 (class 1259 OID 49777)
-- Name: ix_organizations_is_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_organizations_is_active ON public.organizations USING btree (is_active);


--
-- TOC entry 4841 (class 1259 OID 49778)
-- Name: ix_organizations_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_organizations_name ON public.organizations USING btree (name);


--
-- TOC entry 4982 (class 1259 OID 50205)
-- Name: ix_push_device_tokens_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_push_device_tokens_organization_id ON public.push_device_tokens USING btree (organization_id);


--
-- TOC entry 4983 (class 1259 OID 50204)
-- Name: ix_push_device_tokens_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_push_device_tokens_token ON public.push_device_tokens USING btree (token);


--
-- TOC entry 4984 (class 1259 OID 50206)
-- Name: ix_push_device_tokens_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_push_device_tokens_user_id ON public.push_device_tokens USING btree (user_id);


--
-- TOC entry 4987 (class 1259 OID 50216)
-- Name: ix_push_notification_logs_device_token_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_push_notification_logs_device_token_id ON public.push_notification_logs USING btree (device_token_id);


--
-- TOC entry 4988 (class 1259 OID 50215)
-- Name: ix_push_notification_logs_notification_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_push_notification_logs_notification_type ON public.push_notification_logs USING btree (notification_type);


--
-- TOC entry 4989 (class 1259 OID 50214)
-- Name: ix_push_notification_logs_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_push_notification_logs_organization_id ON public.push_notification_logs USING btree (organization_id);


--
-- TOC entry 4990 (class 1259 OID 50218)
-- Name: ix_push_notification_logs_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_push_notification_logs_status ON public.push_notification_logs USING btree (status);


--
-- TOC entry 4991 (class 1259 OID 50217)
-- Name: ix_push_notification_logs_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_push_notification_logs_user_id ON public.push_notification_logs USING btree (user_id);


--
-- TOC entry 4994 (class 1259 OID 50225)
-- Name: ix_push_notification_preferences_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_push_notification_preferences_organization_id ON public.push_notification_preferences USING btree (organization_id);


--
-- TOC entry 4995 (class 1259 OID 50224)
-- Name: ix_push_notification_preferences_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_push_notification_preferences_user_id ON public.push_notification_preferences USING btree (user_id);


--
-- TOC entry 4966 (class 1259 OID 50174)
-- Name: ix_report_distributions_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_report_distributions_organization_id ON public.report_distributions USING btree (organization_id);


--
-- TOC entry 4967 (class 1259 OID 50173)
-- Name: ix_report_distributions_report_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_report_distributions_report_id ON public.report_distributions USING btree (report_id);


--
-- TOC entry 4968 (class 1259 OID 50172)
-- Name: ix_report_distributions_schedule_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_report_distributions_schedule_id ON public.report_distributions USING btree (schedule_id);


--
-- TOC entry 4955 (class 1259 OID 50153)
-- Name: ix_report_schedules_is_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_report_schedules_is_active ON public.report_schedules USING btree (is_active);


--
-- TOC entry 4956 (class 1259 OID 50152)
-- Name: ix_report_schedules_next_run; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_report_schedules_next_run ON public.report_schedules USING btree (next_run);


--
-- TOC entry 4957 (class 1259 OID 50154)
-- Name: ix_report_schedules_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_report_schedules_organization_id ON public.report_schedules USING btree (organization_id);


--
-- TOC entry 4958 (class 1259 OID 50151)
-- Name: ix_report_schedules_template_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_report_schedules_template_id ON public.report_schedules USING btree (template_id);


--
-- TOC entry 4951 (class 1259 OID 50143)
-- Name: ix_report_templates_is_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_report_templates_is_active ON public.report_templates USING btree (is_active);


--
-- TOC entry 4952 (class 1259 OID 50142)
-- Name: ix_report_templates_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_report_templates_organization_id ON public.report_templates USING btree (organization_id);


--
-- TOC entry 4961 (class 1259 OID 50163)
-- Name: ix_reports_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reports_organization_id ON public.reports USING btree (organization_id);


--
-- TOC entry 4962 (class 1259 OID 50162)
-- Name: ix_reports_schedule_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reports_schedule_id ON public.reports USING btree (schedule_id);


--
-- TOC entry 4963 (class 1259 OID 50164)
-- Name: ix_reports_template_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_reports_template_id ON public.reports USING btree (template_id);


--
-- TOC entry 4886 (class 1259 OID 49908)
-- Name: ix_sync_history_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_sync_history_organization_id ON public.sync_history USING btree (organization_id);


--
-- TOC entry 4887 (class 1259 OID 49909)
-- Name: ix_sync_history_platform_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_sync_history_platform_id ON public.sync_history USING btree (platform_id);


--
-- TOC entry 4888 (class 1259 OID 49910)
-- Name: ix_sync_history_started_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_sync_history_started_at ON public.sync_history USING btree (started_at);


--
-- TOC entry 4889 (class 1259 OID 49911)
-- Name: ix_sync_history_sync_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_sync_history_sync_status ON public.sync_history USING btree (sync_status);


--
-- TOC entry 4892 (class 1259 OID 49934)
-- Name: ix_transactions_account_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_transactions_account_id ON public.transactions USING btree (account_id);


--
-- TOC entry 4893 (class 1259 OID 49935)
-- Name: ix_transactions_client_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_transactions_client_id ON public.transactions USING btree (client_id);


--
-- TOC entry 4894 (class 1259 OID 49936)
-- Name: ix_transactions_is_reconciled; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_transactions_is_reconciled ON public.transactions USING btree (is_reconciled);


--
-- TOC entry 4895 (class 1259 OID 49937)
-- Name: ix_transactions_last_synced_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_transactions_last_synced_at ON public.transactions USING btree (last_synced_at);


--
-- TOC entry 4896 (class 1259 OID 49938)
-- Name: ix_transactions_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_transactions_organization_id ON public.transactions USING btree (organization_id);


--
-- TOC entry 4897 (class 1259 OID 49939)
-- Name: ix_transactions_platform_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_transactions_platform_name ON public.transactions USING btree (platform_name);


--
-- TOC entry 4898 (class 1259 OID 49940)
-- Name: ix_transactions_platform_ref; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_transactions_platform_ref ON public.transactions USING btree (platform_name, platform_id);


--
-- TOC entry 4899 (class 1259 OID 49941)
-- Name: ix_transactions_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_transactions_status ON public.transactions USING btree (status);


--
-- TOC entry 4900 (class 1259 OID 49942)
-- Name: ix_transactions_transaction_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_transactions_transaction_date ON public.transactions USING btree (transaction_date);


--
-- TOC entry 4937 (class 1259 OID 50078)
-- Name: ix_trend_analysis_organization_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_trend_analysis_organization_id ON public.trend_analysis USING btree (organization_id);


--
-- TOC entry 4998 (class 2606 OID 49786)
-- Name: accounting_platforms accounting_platforms_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounting_platforms
    ADD CONSTRAINT accounting_platforms_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- TOC entry 4999 (class 2606 OID 49805)
-- Name: accounts accounts_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- TOC entry 5002 (class 2606 OID 49856)
-- Name: ai_analysis_results ai_analysis_results_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ai_analysis_results
    ADD CONSTRAINT ai_analysis_results_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- TOC entry 5003 (class 2606 OID 49861)
-- Name: ai_analysis_results ai_analysis_results_suggested_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ai_analysis_results
    ADD CONSTRAINT ai_analysis_results_suggested_account_id_fkey FOREIGN KEY (suggested_account_id) REFERENCES public.accounts(id) ON DELETE SET NULL;


--
-- TOC entry 5004 (class 2606 OID 49866)
-- Name: ai_analysis_results ai_analysis_results_suggested_account_id_local_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ai_analysis_results
    ADD CONSTRAINT ai_analysis_results_suggested_account_id_local_fkey FOREIGN KEY (suggested_account_id_local) REFERENCES public.accounts(id) ON DELETE SET NULL;


--
-- TOC entry 5000 (class 2606 OID 49822)
-- Name: audit_log audit_log_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- TOC entry 5001 (class 2606 OID 49837)
-- Name: clients clients_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- TOC entry 5005 (class 2606 OID 49882)
-- Name: oauth_tokens oauth_tokens_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.oauth_tokens
    ADD CONSTRAINT oauth_tokens_platform_id_fkey FOREIGN KEY (platform_id) REFERENCES public.accounting_platforms(id) ON DELETE CASCADE;


--
-- TOC entry 5006 (class 2606 OID 49898)
-- Name: sync_history sync_history_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sync_history
    ADD CONSTRAINT sync_history_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- TOC entry 5007 (class 2606 OID 49903)
-- Name: sync_history sync_history_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sync_history
    ADD CONSTRAINT sync_history_platform_id_fkey FOREIGN KEY (platform_id) REFERENCES public.accounting_platforms(id) ON DELETE CASCADE;


--
-- TOC entry 5008 (class 2606 OID 49919)
-- Name: transactions transactions_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.accounts(id) ON DELETE SET NULL;


--
-- TOC entry 5009 (class 2606 OID 49924)
-- Name: transactions transactions_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- TOC entry 5010 (class 2606 OID 49929)
-- Name: transactions transactions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


-- Completed on 2026-01-22 23:53:53

--
-- PostgreSQL database dump complete
--

\unrestrict GXbsElkyvGAhxZymDGcKsTWqxKPPR6ecKLgwnMn7VESnJZxrMUAAoOsAY3FHpb9

