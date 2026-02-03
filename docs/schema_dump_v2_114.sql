--
-- PostgreSQL database dump
--

\restrict h03W5zkfcHWnhgHG5rFukbZctaDbh60hzNLcxr57AjjKq7flpl5KIRhEHdrMql3

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

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
-- Name: cashflow_bucket; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.cashflow_bucket AS ENUM (
    'AR_CURRENT',
    'AR_OVERDUE',
    'AP_CURRENT',
    'AP_OVERDUE',
    'CASH_IN',
    'CASH_OUT',
    'NON_CASH',
    'IGNORE'
);


--
-- Name: date_source; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.date_source AS ENUM (
    'DUE_DATE',
    'TRANSACTION_DATE'
);


--
-- Name: forecastmethod; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.forecastmethod AS ENUM (
    'LINEAR_REGRESSION',
    'MOVING_AVERAGE',
    'EXPONENTIAL_SMOOTHING',
    'SEASONAL_DECOMPOSITION',
    'MANUAL'
);


--
-- Name: forecasttype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.forecasttype AS ENUM (
    'REVENUE',
    'EXPENSE',
    'CASH_FLOW',
    'PROFIT',
    'ACCOUNT_BALANCE'
);


--
-- Name: metrictype; Type: TYPE; Schema: public; Owner: -
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


--
-- Name: normalized_txn_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.normalized_txn_status AS ENUM (
    'DRAFT',
    'AWAITING_APPROVAL',
    'APPROVED',
    'SENT',
    'PAID',
    'VOIDED',
    'UNKNOWN'
);


--
-- Name: normalized_txn_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.normalized_txn_type AS ENUM (
    'SALES_INVOICE',
    'PURCHASE_INVOICE',
    'CREDIT_NOTE',
    'BANK_PAYMENT',
    'BANK_RECEIPT',
    'JOURNAL',
    'TRANSFER',
    'OTHER'
);


--
-- Name: reportformat; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.reportformat AS ENUM (
    'PDF',
    'EXCEL',
    'JSON'
);


--
-- Name: reportfrequency; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.reportfrequency AS ENUM (
    'DAILY',
    'WEEKLY',
    'MONTHLY',
    'QUARTERLY',
    'ANNUAL',
    'ONCE'
);


--
-- Name: trenddirection; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.trenddirection AS ENUM (
    'UPWARD',
    'DOWNWARD',
    'STABLE'
);


--
-- Name: auth_activate_user(uuid, uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.auth_activate_user(p_user_id uuid, p_organization_id uuid) RETURNS boolean
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
        DECLARE
            rows_updated INTEGER;
        BEGIN
            UPDATE public.users
            SET
                organization_id = p_organization_id,
                status = 'active',
                updated_at = now()
            WHERE id = p_user_id AND status = 'pending';
            GET DIAGNOSTICS rows_updated = ROW_COUNT;
            RETURN rows_updated > 0;
        END;
        $$;


--
-- Name: FUNCTION auth_activate_user(p_user_id uuid, p_organization_id uuid); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.auth_activate_user(p_user_id uuid, p_organization_id uuid) IS 'SECURITY DEFINER function for activating pending user with organization. Bypasses RLS. Returns success boolean.';


--
-- Name: auth_create_pending_user(text, text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.auth_create_pending_user(p_email text, p_password_hash text, p_name text) RETURNS uuid
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
        DECLARE
            new_id UUID;
        BEGIN
            INSERT INTO public.users (email, password_hash, name, status, is_active, is_admin)
            VALUES (p_email, p_password_hash, p_name, 'pending', true, false)
            RETURNING id INTO new_id;
            RETURN new_id;
        END;
        $$;


--
-- Name: FUNCTION auth_create_pending_user(p_email text, p_password_hash text, p_name text); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.auth_create_pending_user(p_email text, p_password_hash text, p_name text) IS 'SECURITY DEFINER function for creating pending users during registration. Bypasses RLS. Returns new user UUID.';


--
-- Name: auth_lookup_org_by_id(uuid); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.auth_lookup_org_by_id(lookup_id uuid) RETURNS TABLE(org_id uuid, org_name character varying, org_status character varying)
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
        BEGIN
            RETURN QUERY
            SELECT
                o.id,
                o.name,
                o.status
            FROM public.organizations o
            WHERE o.id = lookup_id
            LIMIT 1;
        END;
        $$;


--
-- Name: FUNCTION auth_lookup_org_by_id(lookup_id uuid); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.auth_lookup_org_by_id(lookup_id uuid) IS 'SECURITY DEFINER function for org lookup during registration. RLS bypass via auth_definer role.';


--
-- Name: auth_lookup_user_by_email(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.auth_lookup_user_by_email(lookup_email text) RETURNS TABLE(user_id uuid, password_hash text, user_status character varying, organization_id uuid, user_role character varying, is_active boolean)
    LANGUAGE plpgsql SECURITY DEFINER
    SET search_path TO 'pg_catalog', 'public'
    AS $$
        BEGIN
            RETURN QUERY
            SELECT
                u.id,
                u.password_hash::TEXT,
                u.status,
                u.organization_id,
                u.role,
                u.is_active
            FROM public.users u
            WHERE lower(u.email) = lower(lookup_email)
            LIMIT 1;
        END;
        $$;


--
-- Name: FUNCTION auth_lookup_user_by_email(lookup_email text); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.auth_lookup_user_by_email(lookup_email text) IS 'SECURITY DEFINER function for auth lookup. This is the ONLY approved RLS bypass for user queries during login. Owned by auth_definer role. Returns minimal fields. Hardened search_path.';


--
-- Name: set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
          NEW.updated_at = now();
          RETURN NEW;
        END;
        $$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accounting_platforms; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.accounting_platforms (
    id uuid NOT NULL,
    organization_id uuid NOT NULL,
    platform_name character varying(50) NOT NULL,
    platform_version character varying(50),
    oauth_client_id character varying(500) NOT NULL,
    client_secret_encrypted bytea NOT NULL,
    access_token_encrypted bytea,
    refresh_token_encrypted bytea,
    token_expires_at timestamp with time zone,
    tenant_id character varying(255),
    realm_id character varying(255),
    is_active boolean DEFAULT true NOT NULL,
    connection_status character varying(50) NOT NULL,
    last_sync_at timestamp with time zone,
    last_error_message character varying(500),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    managed_client_id uuid
);

ALTER TABLE ONLY public.accounting_platforms FORCE ROW LEVEL SECURITY;


--
-- Name: COLUMN accounting_platforms.oauth_client_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.accounting_platforms.oauth_client_id IS 'OAuth client ID from the provider (Xero, QBO). NOT the business client. Renamed from client_id to remove semantic collision.';


--
-- Name: COLUMN accounting_platforms.managed_client_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.accounting_platforms.managed_client_id IS 'Business client whose external accounting realm this connection represents. Composite FK enforces same-org. Nullable during transition; target: NOT NULL for all new connections.';


--
-- Name: accounts; Type: TABLE; Schema: public; Owner: -
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
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    client_id uuid NOT NULL
);

ALTER TABLE ONLY public.accounts FORCE ROW LEVEL SECURITY;


--
-- Name: TABLE accounts; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.accounts IS 'Client-scoped chart of accounts entries. Each client has independent CoA synced from their accounting platform. Enforced: client_id NOT NULL, composite FK to clients, idempotency uniqueness.';


--
-- Name: ai_analysis_results; Type: TABLE; Schema: public; Owner: -
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
    is_approved boolean DEFAULT false NOT NULL,
    was_used boolean DEFAULT false NOT NULL,
    estimated_cost_gbp numeric(7,4),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.ai_analysis_results FORCE ROW LEVEL SECURITY;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(128) NOT NULL
);


--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: -
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

ALTER TABLE ONLY public.audit_log FORCE ROW LEVEL SECURITY;


--
-- Name: cashflow_facts_v1; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cashflow_facts_v1 (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    transaction_id uuid NOT NULL,
    mapping_id integer NOT NULL,
    organization_id uuid NOT NULL,
    client_id uuid,
    normalized_type public.normalized_txn_type NOT NULL,
    normalized_status public.normalized_txn_status NOT NULL,
    canonical_bucket public.cashflow_bucket NOT NULL,
    effective_date date NOT NULL,
    signed_amount numeric(15,2) NOT NULL,
    currency character varying(3) DEFAULT 'GBP'::character varying NOT NULL,
    snapshot_date date DEFAULT CURRENT_DATE NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.cashflow_facts_v1 FORCE ROW LEVEL SECURITY;


--
-- Name: client_assignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.client_assignments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    organization_id uuid NOT NULL,
    client_id uuid NOT NULL,
    user_id uuid NOT NULL,
    assignment_role character varying(50) DEFAULT 'accountant'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    assigned_by uuid,
    assigned_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT client_assignments_assignment_role_check CHECK (((assignment_role)::text = ANY ((ARRAY['primary'::character varying, 'accountant'::character varying, 'reviewer'::character varying, 'backup'::character varying])::text[])))
);

ALTER TABLE ONLY public.client_assignments FORCE ROW LEVEL SECURITY;


--
-- Name: TABLE client_assignments; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.client_assignments IS 'User-to-client workflow assignments. Composite FKs enforce same-org membership at DB level. Assignments are for workload distribution, NOT access control.';


--
-- Name: clients; Type: TABLE; Schema: public; Owner: -
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
    is_active boolean DEFAULT true NOT NULL,
    last_synced_at timestamp with time zone,
    platform_updated_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.clients FORCE ROW LEVEL SECURITY;


--
-- Name: conversion_history; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: currencies; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: dashboard_widgets; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: document_draft; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_draft (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    inbox_item_id uuid NOT NULL,
    org_id uuid NOT NULL,
    status character varying(50) DEFAULT 'draft'::character varying NOT NULL,
    doc_type_guess character varying(50),
    doc_type_confirmed character varying(50),
    counterparty_guess character varying(255),
    counterparty_id uuid,
    doc_date_guess date,
    doc_date_confirmed date,
    currency_guess character varying(3),
    currency_confirmed character varying(3),
    invoice_no_guess character varying(100),
    invoice_no_confirmed character varying(100),
    totals_guess jsonb,
    totals_confirmed jsonb,
    draft_json jsonb,
    validation_json jsonb,
    last_edited_by uuid,
    submitted_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.document_draft FORCE ROW LEVEL SECURITY;


--
-- Name: document_draft_line; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_draft_line (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    draft_id uuid NOT NULL,
    org_id uuid NOT NULL,
    line_no integer DEFAULT 1 NOT NULL,
    description_guess text,
    description_confirmed text,
    qty numeric(15,2) DEFAULT 1.00 NOT NULL,
    unit_price numeric(15,2) DEFAULT 0.00 NOT NULL,
    net numeric(15,2) DEFAULT 0.00 NOT NULL,
    vat numeric(15,2) DEFAULT 0.00 NOT NULL,
    gross numeric(15,2) DEFAULT 0.00 NOT NULL,
    vat_code_guess character varying(50),
    vat_code_confirmed character varying(50),
    nominal_code_guess character varying(50),
    nominal_code_confirmed character varying(50),
    confidence numeric(5,2),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.document_draft_line FORCE ROW LEVEL SECURITY;


--
-- Name: document_inbox_item; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_inbox_item (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    org_id uuid NOT NULL,
    uploaded_by_user_id uuid,
    source_type character varying(50) DEFAULT 'upload'::character varying NOT NULL,
    file_name character varying(255) NOT NULL,
    mime_type character varying(100),
    file_path text NOT NULL,
    checksum_hash character varying(64) NOT NULL,
    status character varying(50) DEFAULT 'uploaded'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.document_inbox_item FORCE ROW LEVEL SECURITY;


--
-- Name: document_ocr_result; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.document_ocr_result (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    inbox_item_id uuid NOT NULL,
    org_id uuid NOT NULL,
    ocr_engine character varying(50) DEFAULT 'stub'::character varying NOT NULL,
    raw_text text DEFAULT ''::text NOT NULL,
    layout_json jsonb,
    pages integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY public.document_ocr_result FORCE ROW LEVEL SECURITY;


--
-- Name: exchange_rates; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: financial_metrics; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: forecasts; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: ingestion_quarantine; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ingestion_quarantine (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    transaction_id uuid NOT NULL,
    organization_id uuid NOT NULL,
    platform_name character varying(50) NOT NULL,
    source_type character varying(100) NOT NULL,
    source_status character varying(100) NOT NULL,
    reason text NOT NULL,
    quarantined_at timestamp with time zone DEFAULT now() NOT NULL,
    resolved_at timestamp with time zone,
    resolved_by character varying(255)
);

ALTER TABLE ONLY public.ingestion_quarantine FORCE ROW LEVEL SECURITY;


--
-- Name: kpis; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: -
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
    is_reconciled boolean DEFAULT false NOT NULL,
    last_synced_at timestamp with time zone,
    platform_updated_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_transactions_currency_iso CHECK (((currency)::text ~ '^[A-Z]{3}$'::text)),
    CONSTRAINT ck_transactions_tax_nonnegative CHECK ((tax_amount >= (0)::numeric)),
    CONSTRAINT ck_transactions_total_matches CHECK ((total_amount = (amount + tax_amount)))
);

ALTER TABLE ONLY public.transactions FORCE ROW LEVEL SECURITY;


--
-- Name: mapping_coverage_stats; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.mapping_coverage_stats AS
 SELECT t.organization_id,
    t.platform_name,
    (count(*))::integer AS total_transactions,
    (count(f.id))::integer AS mapped_count,
    (count(q.id))::integer AS quarantined_count,
    (((count(*) - count(f.id)) - count(q.id)))::integer AS unmapped_count,
        CASE
            WHEN (count(*) = 0) THEN 0.0
            ELSE round((((count(f.id))::numeric / (count(*))::numeric) * (100)::numeric), 2)
        END AS coverage_pct
   FROM ((public.transactions t
     LEFT JOIN public.cashflow_facts_v1 f ON ((f.transaction_id = t.id)))
     LEFT JOIN public.ingestion_quarantine q ON (((q.transaction_id = t.id) AND (q.resolved_at IS NULL))))
  GROUP BY t.organization_id, t.platform_name;


--
-- Name: mobile_sessions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: oauth_tokens; Type: TABLE; Schema: public; Owner: -
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

ALTER TABLE ONLY public.oauth_tokens FORCE ROW LEVEL SECURITY;


--
-- Name: offline_sync_queue; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: organizations; Type: TABLE; Schema: public; Owner: -
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
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_organizations_currency_iso CHECK (((currency)::text ~ '^[A-Z]{3}$'::text))
);

ALTER TABLE ONLY public.organizations FORCE ROW LEVEL SECURITY;


--
-- Name: platform_transaction_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.platform_transaction_mapping (
    id integer NOT NULL,
    platform_name character varying(50) NOT NULL,
    source_type character varying(100) NOT NULL,
    source_status character varying(100) NOT NULL,
    normalized_type public.normalized_txn_type NOT NULL,
    normalized_status public.normalized_txn_status NOT NULL,
    canonical_bucket public.cashflow_bucket NOT NULL,
    effective_date_source public.date_source DEFAULT 'TRANSACTION_DATE'::public.date_source NOT NULL,
    priority integer DEFAULT 0 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: platform_transaction_mapping_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.platform_transaction_mapping_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: platform_transaction_mapping_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.platform_transaction_mapping_id_seq OWNED BY public.platform_transaction_mapping.id;


--
-- Name: push_device_tokens; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: push_notification_logs; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: push_notification_preferences; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: report_distributions; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: report_schedules; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: report_templates; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: reports; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: sync_history; Type: TABLE; Schema: public; Owner: -
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

ALTER TABLE ONLY public.sync_history FORCE ROW LEVEL SECURITY;


--
-- Name: tax_adjustments; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: tax_compliance_logs; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: tax_liabilities; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: tax_rates; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: tax_types; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: trend_analysis; Type: TABLE; Schema: public; Owner: -
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


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    is_admin boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_login timestamp with time zone,
    organization_id uuid,
    role character varying(50) DEFAULT 'viewer'::character varying NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    CONSTRAINT ck_users_org_status CHECK (((((status)::text = 'pending'::text) AND (organization_id IS NULL)) OR (((status)::text <> 'pending'::text) AND (organization_id IS NOT NULL)))),
    CONSTRAINT ck_users_status_values CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'active'::character varying, 'suspended'::character varying, 'disabled'::character varying])::text[])))
);

ALTER TABLE ONLY public.users FORCE ROW LEVEL SECURITY;


--
-- Name: COLUMN users.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.status IS 'User lifecycle status. Pending users have NULL org_id (registration in progress). Active/suspended/disabled users must have org_id.';


--
-- Name: CONSTRAINT ck_users_org_status ON users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON CONSTRAINT ck_users_org_status ON public.users IS 'DB-enforced invariant: pending users may have NULL org; non-pending users must have org. Prevents active users without tenant context.';


--
-- Name: platform_transaction_mapping id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform_transaction_mapping ALTER COLUMN id SET DEFAULT nextval('public.platform_transaction_mapping_id_seq'::regclass);


--
-- Name: accounting_platforms accounting_platforms_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounting_platforms
    ADD CONSTRAINT accounting_platforms_pkey PRIMARY KEY (id);


--
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (id);


--
-- Name: ai_analysis_results ai_analysis_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_analysis_results
    ADD CONSTRAINT ai_analysis_results_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: cashflow_facts_v1 cashflow_facts_v1_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cashflow_facts_v1
    ADD CONSTRAINT cashflow_facts_v1_pkey PRIMARY KEY (id);


--
-- Name: client_assignments client_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_assignments
    ADD CONSTRAINT client_assignments_pkey PRIMARY KEY (id);


--
-- Name: clients clients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_pkey PRIMARY KEY (id);


--
-- Name: conversion_history conversion_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversion_history
    ADD CONSTRAINT conversion_history_pkey PRIMARY KEY (id);


--
-- Name: currencies currencies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.currencies
    ADD CONSTRAINT currencies_pkey PRIMARY KEY (id);


--
-- Name: dashboard_widgets dashboard_widgets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dashboard_widgets
    ADD CONSTRAINT dashboard_widgets_pkey PRIMARY KEY (id);


--
-- Name: document_draft document_draft_inbox_item_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_draft
    ADD CONSTRAINT document_draft_inbox_item_id_key UNIQUE (inbox_item_id);


--
-- Name: document_draft_line document_draft_line_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_draft_line
    ADD CONSTRAINT document_draft_line_pkey PRIMARY KEY (id);


--
-- Name: document_draft document_draft_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_draft
    ADD CONSTRAINT document_draft_pkey PRIMARY KEY (id);


--
-- Name: document_inbox_item document_inbox_item_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_inbox_item
    ADD CONSTRAINT document_inbox_item_pkey PRIMARY KEY (id);


--
-- Name: document_ocr_result document_ocr_result_inbox_item_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_ocr_result
    ADD CONSTRAINT document_ocr_result_inbox_item_id_key UNIQUE (inbox_item_id);


--
-- Name: document_ocr_result document_ocr_result_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_ocr_result
    ADD CONSTRAINT document_ocr_result_pkey PRIMARY KEY (id);


--
-- Name: exchange_rates exchange_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exchange_rates
    ADD CONSTRAINT exchange_rates_pkey PRIMARY KEY (id);


--
-- Name: financial_metrics financial_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.financial_metrics
    ADD CONSTRAINT financial_metrics_pkey PRIMARY KEY (id);


--
-- Name: forecasts forecasts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.forecasts
    ADD CONSTRAINT forecasts_pkey PRIMARY KEY (id);


--
-- Name: ingestion_quarantine ingestion_quarantine_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_quarantine
    ADD CONSTRAINT ingestion_quarantine_pkey PRIMARY KEY (id);


--
-- Name: kpis kpis_org_code_date_unique; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kpis
    ADD CONSTRAINT kpis_org_code_date_unique UNIQUE (organization_id, code, period_date);


--
-- Name: kpis kpis_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kpis
    ADD CONSTRAINT kpis_pkey PRIMARY KEY (id);


--
-- Name: mobile_sessions mobile_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mobile_sessions
    ADD CONSTRAINT mobile_sessions_pkey PRIMARY KEY (id);


--
-- Name: oauth_tokens oauth_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oauth_tokens
    ADD CONSTRAINT oauth_tokens_pkey PRIMARY KEY (id);


--
-- Name: offline_sync_queue offline_sync_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.offline_sync_queue
    ADD CONSTRAINT offline_sync_queue_pkey PRIMARY KEY (id);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- Name: platform_transaction_mapping platform_transaction_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform_transaction_mapping
    ADD CONSTRAINT platform_transaction_mapping_pkey PRIMARY KEY (id);


--
-- Name: push_device_tokens push_device_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.push_device_tokens
    ADD CONSTRAINT push_device_tokens_pkey PRIMARY KEY (id);


--
-- Name: push_notification_logs push_notification_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.push_notification_logs
    ADD CONSTRAINT push_notification_logs_pkey PRIMARY KEY (id);


--
-- Name: push_notification_preferences push_notification_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.push_notification_preferences
    ADD CONSTRAINT push_notification_preferences_pkey PRIMARY KEY (id);


--
-- Name: report_distributions report_distributions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.report_distributions
    ADD CONSTRAINT report_distributions_pkey PRIMARY KEY (id);


--
-- Name: report_schedules report_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.report_schedules
    ADD CONSTRAINT report_schedules_pkey PRIMARY KEY (id);


--
-- Name: report_templates report_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.report_templates
    ADD CONSTRAINT report_templates_pkey PRIMARY KEY (id);


--
-- Name: reports reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_pkey PRIMARY KEY (id);


--
-- Name: sync_history sync_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_history
    ADD CONSTRAINT sync_history_pkey PRIMARY KEY (id);


--
-- Name: tax_adjustments tax_adjustments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tax_adjustments
    ADD CONSTRAINT tax_adjustments_pkey PRIMARY KEY (id);


--
-- Name: tax_compliance_logs tax_compliance_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tax_compliance_logs
    ADD CONSTRAINT tax_compliance_logs_pkey PRIMARY KEY (id);


--
-- Name: tax_liabilities tax_liabilities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tax_liabilities
    ADD CONSTRAINT tax_liabilities_pkey PRIMARY KEY (id);


--
-- Name: tax_rates tax_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tax_rates
    ADD CONSTRAINT tax_rates_pkey PRIMARY KEY (id);


--
-- Name: tax_types tax_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tax_types
    ADD CONSTRAINT tax_types_pkey PRIMARY KEY (id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- Name: trend_analysis trend_analysis_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trend_analysis
    ADD CONSTRAINT trend_analysis_pkey PRIMARY KEY (id);


--
-- Name: accounting_platforms uq_accounting_platforms_org_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounting_platforms
    ADD CONSTRAINT uq_accounting_platforms_org_id UNIQUE (organization_id, id);


--
-- Name: client_assignments uq_client_assignments_client_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_assignments
    ADD CONSTRAINT uq_client_assignments_client_user UNIQUE (client_id, user_id);


--
-- Name: clients uq_clients_org_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT uq_clients_org_id UNIQUE (organization_id, id);


--
-- Name: currencies uq_currency_org_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.currencies
    ADD CONSTRAINT uq_currency_org_code UNIQUE (organization_id, code);


--
-- Name: exchange_rates uq_exchange_rate_org_pair_date_source; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.exchange_rates
    ADD CONSTRAINT uq_exchange_rate_org_pair_date_source UNIQUE (organization_id, source_currency_code, target_currency_code, effective_date, source);


--
-- Name: tax_liabilities uq_tax_liability_org_type_year_period; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tax_liabilities
    ADD CONSTRAINT uq_tax_liability_org_type_year_period UNIQUE (organization_id, tax_type_id, tax_year, period);


--
-- Name: tax_rates uq_tax_rate_org_type_juris_date; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tax_rates
    ADD CONSTRAINT uq_tax_rate_org_type_juris_date UNIQUE (organization_id, tax_type_id, jurisdiction, effective_date);


--
-- Name: tax_types uq_tax_type_org_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tax_types
    ADD CONSTRAINT uq_tax_type_org_code UNIQUE (organization_id, code);


--
-- Name: users uq_users_org_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT uq_users_org_id UNIQUE (organization_id, id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_accounting_platforms_connection_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounting_platforms_connection_status ON public.accounting_platforms USING btree (connection_status);


--
-- Name: ix_accounting_platforms_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounting_platforms_is_active ON public.accounting_platforms USING btree (is_active);


--
-- Name: ix_accounting_platforms_last_sync_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounting_platforms_last_sync_at ON public.accounting_platforms USING btree (last_sync_at);


--
-- Name: ix_accounting_platforms_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounting_platforms_organization_id ON public.accounting_platforms USING btree (organization_id);


--
-- Name: ix_accounting_platforms_platform_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounting_platforms_platform_name ON public.accounting_platforms USING btree (platform_name);


--
-- Name: ix_accounting_platforms_realm_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounting_platforms_realm_id ON public.accounting_platforms USING btree (realm_id);


--
-- Name: ix_accounting_platforms_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounting_platforms_tenant_id ON public.accounting_platforms USING btree (tenant_id);


--
-- Name: ix_accounts_account_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounts_account_type ON public.accounts USING btree (account_type);


--
-- Name: ix_accounts_client_code; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_accounts_client_code ON public.accounts USING btree (client_id, code);


--
-- Name: ix_accounts_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounts_client_id ON public.accounts USING btree (client_id);


--
-- Name: ix_accounts_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounts_name ON public.accounts USING btree (name);


--
-- Name: ix_accounts_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounts_organization_id ON public.accounts USING btree (organization_id);


--
-- Name: ix_accounts_platform_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_accounts_platform_name ON public.accounts USING btree (platform_name);


--
-- Name: ix_ai_analysis_results_analysis_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_analysis_results_analysis_type ON public.ai_analysis_results USING btree (analysis_type);


--
-- Name: ix_ai_analysis_results_is_approved; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_analysis_results_is_approved ON public.ai_analysis_results USING btree (is_approved);


--
-- Name: ix_ai_analysis_results_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_analysis_results_organization_id ON public.ai_analysis_results USING btree (organization_id);


--
-- Name: ix_ai_analysis_results_suggested_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_analysis_results_suggested_account_id ON public.ai_analysis_results USING btree (suggested_account_id);


--
-- Name: ix_ai_analysis_results_suggested_account_id_local; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_analysis_results_suggested_account_id_local ON public.ai_analysis_results USING btree (suggested_account_id_local);


--
-- Name: ix_ai_analysis_results_target_entity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ai_analysis_results_target_entity_id ON public.ai_analysis_results USING btree (target_entity_id);


--
-- Name: ix_audit_log_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_log_created_at ON public.audit_log USING btree (created_at);


--
-- Name: ix_audit_log_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_log_organization_id ON public.audit_log USING btree (organization_id);


--
-- Name: ix_audit_log_table_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_log_table_name ON public.audit_log USING btree (table_name);


--
-- Name: ix_cf_facts_client_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cf_facts_client_date ON public.cashflow_facts_v1 USING btree (client_id, effective_date);


--
-- Name: ix_cf_facts_org_bucket_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cf_facts_org_bucket_date ON public.cashflow_facts_v1 USING btree (organization_id, canonical_bucket, effective_date);


--
-- Name: ix_cf_facts_org_effective_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cf_facts_org_effective_date ON public.cashflow_facts_v1 USING btree (organization_id, effective_date);


--
-- Name: ix_cf_facts_transaction_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_cf_facts_transaction_id ON public.cashflow_facts_v1 USING btree (transaction_id);


--
-- Name: ix_client_assignments_client_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_client_assignments_client_active ON public.client_assignments USING btree (client_id) WHERE (is_active = true);


--
-- Name: ix_client_assignments_org; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_client_assignments_org ON public.client_assignments USING btree (organization_id);


--
-- Name: ix_client_assignments_org_user_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_client_assignments_org_user_active ON public.client_assignments USING btree (organization_id, user_id) WHERE (is_active = true);


--
-- Name: ix_client_assignments_user_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_client_assignments_user_active ON public.client_assignments USING btree (user_id) WHERE (is_active = true);


--
-- Name: ix_clients_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clients_email ON public.clients USING btree (email);


--
-- Name: ix_clients_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clients_is_active ON public.clients USING btree (is_active);


--
-- Name: ix_clients_last_synced_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clients_last_synced_at ON public.clients USING btree (last_synced_at);


--
-- Name: ix_clients_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clients_name ON public.clients USING btree (name);


--
-- Name: ix_clients_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clients_organization_id ON public.clients USING btree (organization_id);


--
-- Name: ix_clients_platform_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_clients_platform_name ON public.clients USING btree (platform_name);


--
-- Name: ix_dashboard_widgets_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dashboard_widgets_is_active ON public.dashboard_widgets USING btree (is_active);


--
-- Name: ix_dashboard_widgets_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dashboard_widgets_organization_id ON public.dashboard_widgets USING btree (organization_id);


--
-- Name: ix_document_draft_counterparty; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_document_draft_counterparty ON public.document_draft USING btree (counterparty_id);


--
-- Name: ix_document_draft_last_editor; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_document_draft_last_editor ON public.document_draft USING btree (last_edited_by);


--
-- Name: ix_document_draft_line_draft_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_document_draft_line_draft_id ON public.document_draft_line USING btree (draft_id);


--
-- Name: ix_document_draft_line_org_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_document_draft_line_org_id ON public.document_draft_line USING btree (org_id);


--
-- Name: ix_document_draft_org_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_document_draft_org_id ON public.document_draft USING btree (org_id);


--
-- Name: ix_document_draft_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_document_draft_status ON public.document_draft USING btree (status);


--
-- Name: ix_document_draft_submitted_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_document_draft_submitted_by ON public.document_draft USING btree (submitted_by);


--
-- Name: ix_document_inbox_org_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_document_inbox_org_id ON public.document_inbox_item USING btree (org_id);


--
-- Name: ix_document_inbox_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_document_inbox_status ON public.document_inbox_item USING btree (status);


--
-- Name: ix_document_inbox_uploaded_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_document_inbox_uploaded_by ON public.document_inbox_item USING btree (uploaded_by_user_id);


--
-- Name: ix_document_ocr_org_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_document_ocr_org_id ON public.document_ocr_result USING btree (org_id);


--
-- Name: ix_financial_metrics_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_financial_metrics_organization_id ON public.financial_metrics USING btree (organization_id);


--
-- Name: ix_financial_metrics_period_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_financial_metrics_period_date ON public.financial_metrics USING btree (period_date);


--
-- Name: ix_forecasts_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forecasts_is_active ON public.forecasts USING btree (is_active);


--
-- Name: ix_forecasts_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_forecasts_organization_id ON public.forecasts USING btree (organization_id);


--
-- Name: ix_kpis_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kpis_is_active ON public.kpis USING btree (is_active);


--
-- Name: ix_kpis_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kpis_organization_id ON public.kpis USING btree (organization_id);


--
-- Name: ix_kpis_period_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kpis_period_date ON public.kpis USING btree (period_date);


--
-- Name: ix_mobile_sessions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mobile_sessions_organization_id ON public.mobile_sessions USING btree (organization_id);


--
-- Name: ix_mobile_sessions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mobile_sessions_user_id ON public.mobile_sessions USING btree (user_id);


--
-- Name: ix_oauth_tokens_expires_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_oauth_tokens_expires_at ON public.oauth_tokens USING btree (expires_at);


--
-- Name: ix_oauth_tokens_is_revoked; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_oauth_tokens_is_revoked ON public.oauth_tokens USING btree (is_revoked);


--
-- Name: ix_oauth_tokens_issued_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_oauth_tokens_issued_at ON public.oauth_tokens USING btree (issued_at);


--
-- Name: ix_oauth_tokens_platform_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_oauth_tokens_platform_id ON public.oauth_tokens USING btree (platform_id);


--
-- Name: ix_offline_sync_queue_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_offline_sync_queue_action ON public.offline_sync_queue USING btree (action);


--
-- Name: ix_offline_sync_queue_entity_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_offline_sync_queue_entity_type ON public.offline_sync_queue USING btree (entity_type);


--
-- Name: ix_offline_sync_queue_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_offline_sync_queue_organization_id ON public.offline_sync_queue USING btree (organization_id);


--
-- Name: ix_offline_sync_queue_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_offline_sync_queue_status ON public.offline_sync_queue USING btree (status);


--
-- Name: ix_offline_sync_queue_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_offline_sync_queue_user_id ON public.offline_sync_queue USING btree (user_id);


--
-- Name: ix_organizations_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_organizations_created_at ON public.organizations USING btree (created_at);


--
-- Name: ix_organizations_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_organizations_email ON public.organizations USING btree (email);


--
-- Name: ix_organizations_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_organizations_is_active ON public.organizations USING btree (is_active);


--
-- Name: ix_organizations_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_organizations_name ON public.organizations USING btree (name);


--
-- Name: ix_ptm_platform_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ptm_platform_name ON public.platform_transaction_mapping USING btree (platform_name);


--
-- Name: ix_ptm_platform_type_status_active; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_ptm_platform_type_status_active ON public.platform_transaction_mapping USING btree (platform_name, source_type, source_status) WHERE (is_active = true);


--
-- Name: ix_push_device_tokens_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_push_device_tokens_organization_id ON public.push_device_tokens USING btree (organization_id);


--
-- Name: ix_push_device_tokens_token; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_push_device_tokens_token ON public.push_device_tokens USING btree (token);


--
-- Name: ix_push_device_tokens_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_push_device_tokens_user_id ON public.push_device_tokens USING btree (user_id);


--
-- Name: ix_push_notification_logs_device_token_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_push_notification_logs_device_token_id ON public.push_notification_logs USING btree (device_token_id);


--
-- Name: ix_push_notification_logs_notification_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_push_notification_logs_notification_type ON public.push_notification_logs USING btree (notification_type);


--
-- Name: ix_push_notification_logs_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_push_notification_logs_organization_id ON public.push_notification_logs USING btree (organization_id);


--
-- Name: ix_push_notification_logs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_push_notification_logs_status ON public.push_notification_logs USING btree (status);


--
-- Name: ix_push_notification_logs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_push_notification_logs_user_id ON public.push_notification_logs USING btree (user_id);


--
-- Name: ix_push_notification_preferences_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_push_notification_preferences_organization_id ON public.push_notification_preferences USING btree (organization_id);


--
-- Name: ix_push_notification_preferences_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_push_notification_preferences_user_id ON public.push_notification_preferences USING btree (user_id);


--
-- Name: ix_quarantine_org_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quarantine_org_id ON public.ingestion_quarantine USING btree (organization_id);


--
-- Name: ix_quarantine_txn_unresolved; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_quarantine_txn_unresolved ON public.ingestion_quarantine USING btree (transaction_id) WHERE (resolved_at IS NULL);


--
-- Name: ix_report_distributions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_report_distributions_organization_id ON public.report_distributions USING btree (organization_id);


--
-- Name: ix_report_distributions_report_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_report_distributions_report_id ON public.report_distributions USING btree (report_id);


--
-- Name: ix_report_distributions_schedule_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_report_distributions_schedule_id ON public.report_distributions USING btree (schedule_id);


--
-- Name: ix_report_schedules_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_report_schedules_is_active ON public.report_schedules USING btree (is_active);


--
-- Name: ix_report_schedules_next_run; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_report_schedules_next_run ON public.report_schedules USING btree (next_run);


--
-- Name: ix_report_schedules_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_report_schedules_organization_id ON public.report_schedules USING btree (organization_id);


--
-- Name: ix_report_schedules_template_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_report_schedules_template_id ON public.report_schedules USING btree (template_id);


--
-- Name: ix_report_templates_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_report_templates_is_active ON public.report_templates USING btree (is_active);


--
-- Name: ix_report_templates_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_report_templates_organization_id ON public.report_templates USING btree (organization_id);


--
-- Name: ix_reports_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reports_organization_id ON public.reports USING btree (organization_id);


--
-- Name: ix_reports_schedule_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reports_schedule_id ON public.reports USING btree (schedule_id);


--
-- Name: ix_reports_template_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reports_template_id ON public.reports USING btree (template_id);


--
-- Name: ix_sync_history_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sync_history_organization_id ON public.sync_history USING btree (organization_id);


--
-- Name: ix_sync_history_platform_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sync_history_platform_id ON public.sync_history USING btree (platform_id);


--
-- Name: ix_sync_history_started_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sync_history_started_at ON public.sync_history USING btree (started_at);


--
-- Name: ix_sync_history_sync_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sync_history_sync_status ON public.sync_history USING btree (sync_status);


--
-- Name: ix_transactions_account_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transactions_account_id ON public.transactions USING btree (account_id);


--
-- Name: ix_transactions_client_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transactions_client_id ON public.transactions USING btree (client_id);


--
-- Name: ix_transactions_is_reconciled; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transactions_is_reconciled ON public.transactions USING btree (is_reconciled);


--
-- Name: ix_transactions_last_synced_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transactions_last_synced_at ON public.transactions USING btree (last_synced_at);


--
-- Name: ix_transactions_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transactions_organization_id ON public.transactions USING btree (organization_id);


--
-- Name: ix_transactions_platform_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transactions_platform_name ON public.transactions USING btree (platform_name);


--
-- Name: ix_transactions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transactions_status ON public.transactions USING btree (status);


--
-- Name: ix_transactions_transaction_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transactions_transaction_date ON public.transactions USING btree (transaction_date);


--
-- Name: ix_trend_analysis_organization_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trend_analysis_organization_id ON public.trend_analysis USING btree (organization_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ux_accounts_client_platform_idempotency; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_accounts_client_platform_idempotency ON public.accounts USING btree (client_id, platform_name, platform_id);


--
-- Name: ux_clients_org_platform; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_clients_org_platform ON public.clients USING btree (organization_id, platform_name, platform_id);


--
-- Name: ux_transactions_org_platform; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_transactions_org_platform ON public.transactions USING btree (organization_id, platform_name, platform_id);


--
-- Name: ux_users_email_lower; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ux_users_email_lower ON public.users USING btree (lower((email)::text));


--
-- Name: INDEX ux_users_email_lower; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON INDEX public.ux_users_email_lower IS 'Case-insensitive email uniqueness. Prevents duplicate identities differing only by case. Auth lookup must use lower(email).';


--
-- Name: client_assignments set_updated_at_client_assignments; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER set_updated_at_client_assignments BEFORE UPDATE ON public.client_assignments FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: accounting_platforms trg_accounting_platforms_set_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_accounting_platforms_set_updated_at BEFORE UPDATE ON public.accounting_platforms FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: accounts trg_accounts_set_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_accounts_set_updated_at BEFORE UPDATE ON public.accounts FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: ai_analysis_results trg_ai_analysis_results_set_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_ai_analysis_results_set_updated_at BEFORE UPDATE ON public.ai_analysis_results FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: clients trg_clients_set_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_clients_set_updated_at BEFORE UPDATE ON public.clients FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: organizations trg_organizations_set_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_organizations_set_updated_at BEFORE UPDATE ON public.organizations FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: transactions trg_transactions_set_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_transactions_set_updated_at BEFORE UPDATE ON public.transactions FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: accounting_platforms accounting_platforms_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounting_platforms
    ADD CONSTRAINT accounting_platforms_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: accounts accounts_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: ai_analysis_results ai_analysis_results_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_analysis_results
    ADD CONSTRAINT ai_analysis_results_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: ai_analysis_results ai_analysis_results_suggested_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_analysis_results
    ADD CONSTRAINT ai_analysis_results_suggested_account_id_fkey FOREIGN KEY (suggested_account_id) REFERENCES public.accounts(id) ON DELETE SET NULL;


--
-- Name: ai_analysis_results ai_analysis_results_suggested_account_id_local_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_analysis_results
    ADD CONSTRAINT ai_analysis_results_suggested_account_id_local_fkey FOREIGN KEY (suggested_account_id_local) REFERENCES public.accounts(id) ON DELETE SET NULL;


--
-- Name: audit_log audit_log_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: cashflow_facts_v1 cashflow_facts_v1_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cashflow_facts_v1
    ADD CONSTRAINT cashflow_facts_v1_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: cashflow_facts_v1 cashflow_facts_v1_mapping_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cashflow_facts_v1
    ADD CONSTRAINT cashflow_facts_v1_mapping_id_fkey FOREIGN KEY (mapping_id) REFERENCES public.platform_transaction_mapping(id);


--
-- Name: cashflow_facts_v1 cashflow_facts_v1_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cashflow_facts_v1
    ADD CONSTRAINT cashflow_facts_v1_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: cashflow_facts_v1 cashflow_facts_v1_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cashflow_facts_v1
    ADD CONSTRAINT cashflow_facts_v1_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id) ON DELETE CASCADE;


--
-- Name: clients clients_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.clients
    ADD CONSTRAINT clients_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: document_draft document_draft_counterparty_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_draft
    ADD CONSTRAINT document_draft_counterparty_id_fkey FOREIGN KEY (counterparty_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: document_draft document_draft_inbox_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_draft
    ADD CONSTRAINT document_draft_inbox_item_id_fkey FOREIGN KEY (inbox_item_id) REFERENCES public.document_inbox_item(id) ON DELETE CASCADE;


--
-- Name: document_draft document_draft_last_edited_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_draft
    ADD CONSTRAINT document_draft_last_edited_by_fkey FOREIGN KEY (last_edited_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: document_draft_line document_draft_line_draft_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_draft_line
    ADD CONSTRAINT document_draft_line_draft_id_fkey FOREIGN KEY (draft_id) REFERENCES public.document_draft(id) ON DELETE CASCADE;


--
-- Name: document_draft_line document_draft_line_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_draft_line
    ADD CONSTRAINT document_draft_line_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: document_draft document_draft_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_draft
    ADD CONSTRAINT document_draft_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: document_draft document_draft_submitted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_draft
    ADD CONSTRAINT document_draft_submitted_by_fkey FOREIGN KEY (submitted_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: document_inbox_item document_inbox_item_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_inbox_item
    ADD CONSTRAINT document_inbox_item_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: document_inbox_item document_inbox_item_uploaded_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_inbox_item
    ADD CONSTRAINT document_inbox_item_uploaded_by_user_id_fkey FOREIGN KEY (uploaded_by_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: document_ocr_result document_ocr_result_inbox_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_ocr_result
    ADD CONSTRAINT document_ocr_result_inbox_item_id_fkey FOREIGN KEY (inbox_item_id) REFERENCES public.document_inbox_item(id) ON DELETE CASCADE;


--
-- Name: document_ocr_result document_ocr_result_org_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.document_ocr_result
    ADD CONSTRAINT document_ocr_result_org_id_fkey FOREIGN KEY (org_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: accounting_platforms fk_accounting_platforms_managed_client; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounting_platforms
    ADD CONSTRAINT fk_accounting_platforms_managed_client FOREIGN KEY (organization_id, managed_client_id) REFERENCES public.clients(organization_id, id) ON DELETE SET NULL;


--
-- Name: CONSTRAINT fk_accounting_platforms_managed_client ON accounting_platforms; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON CONSTRAINT fk_accounting_platforms_managed_client ON public.accounting_platforms IS 'Composite FK ensures managed business client belongs to same organization. Declarative enforcement, no trigger required.';


--
-- Name: accounts fk_accounts_client; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT fk_accounts_client FOREIGN KEY (organization_id, client_id) REFERENCES public.clients(organization_id, id) ON DELETE CASCADE;


--
-- Name: CONSTRAINT fk_accounts_client ON accounts; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON CONSTRAINT fk_accounts_client ON public.accounts IS 'Composite FK enforces account belongs to same organization as its client. Prevents cross-org data leakage.';


--
-- Name: accounts fk_accounts_client_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT fk_accounts_client_id FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE CASCADE;


--
-- Name: client_assignments fk_client_assignments_assigner; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_assignments
    ADD CONSTRAINT fk_client_assignments_assigner FOREIGN KEY (organization_id, assigned_by) REFERENCES public.users(organization_id, id) ON DELETE SET NULL;


--
-- Name: client_assignments fk_client_assignments_client; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_assignments
    ADD CONSTRAINT fk_client_assignments_client FOREIGN KEY (organization_id, client_id) REFERENCES public.clients(organization_id, id) ON DELETE CASCADE;


--
-- Name: CONSTRAINT fk_client_assignments_client ON client_assignments; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON CONSTRAINT fk_client_assignments_client ON public.client_assignments IS 'Composite FK ensures client belongs to same organization as assignment.';


--
-- Name: client_assignments fk_client_assignments_org; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_assignments
    ADD CONSTRAINT fk_client_assignments_org FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: client_assignments fk_client_assignments_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_assignments
    ADD CONSTRAINT fk_client_assignments_user FOREIGN KEY (organization_id, user_id) REFERENCES public.users(organization_id, id) ON DELETE CASCADE;


--
-- Name: CONSTRAINT fk_client_assignments_user ON client_assignments; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON CONSTRAINT fk_client_assignments_user ON public.client_assignments IS 'Composite FK ensures user belongs to same organization as assignment.';


--
-- Name: ingestion_quarantine ingestion_quarantine_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_quarantine
    ADD CONSTRAINT ingestion_quarantine_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: ingestion_quarantine ingestion_quarantine_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_quarantine
    ADD CONSTRAINT ingestion_quarantine_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(id) ON DELETE CASCADE;


--
-- Name: oauth_tokens oauth_tokens_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.oauth_tokens
    ADD CONSTRAINT oauth_tokens_platform_id_fkey FOREIGN KEY (platform_id) REFERENCES public.accounting_platforms(id) ON DELETE CASCADE;


--
-- Name: sync_history sync_history_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_history
    ADD CONSTRAINT sync_history_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: sync_history sync_history_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sync_history
    ADD CONSTRAINT sync_history_platform_id_fkey FOREIGN KEY (platform_id) REFERENCES public.accounting_platforms(id) ON DELETE CASCADE;


--
-- Name: transactions transactions_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.accounts(id) ON DELETE SET NULL;


--
-- Name: transactions transactions_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.clients(id) ON DELETE SET NULL;


--
-- Name: transactions transactions_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: users users_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE CASCADE;


--
-- Name: accounting_platforms; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.accounting_platforms ENABLE ROW LEVEL SECURITY;

--
-- Name: accounts; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.accounts ENABLE ROW LEVEL SECURITY;

--
-- Name: ai_analysis_results; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.ai_analysis_results ENABLE ROW LEVEL SECURITY;

--
-- Name: audit_log; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;

--
-- Name: cashflow_facts_v1; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.cashflow_facts_v1 ENABLE ROW LEVEL SECURITY;

--
-- Name: client_assignments; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.client_assignments ENABLE ROW LEVEL SECURITY;

--
-- Name: clients; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.clients ENABLE ROW LEVEL SECURITY;

--
-- Name: document_draft; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.document_draft ENABLE ROW LEVEL SECURITY;

--
-- Name: document_draft_line; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.document_draft_line ENABLE ROW LEVEL SECURITY;

--
-- Name: document_inbox_item; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.document_inbox_item ENABLE ROW LEVEL SECURITY;

--
-- Name: document_ocr_result; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.document_ocr_result ENABLE ROW LEVEL SECURITY;

--
-- Name: ingestion_quarantine; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.ingestion_quarantine ENABLE ROW LEVEL SECURITY;

--
-- Name: oauth_tokens; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.oauth_tokens ENABLE ROW LEVEL SECURITY;

--
-- Name: organizations; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;

--
-- Name: accounting_platforms p_accounting_platforms_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_accounting_platforms_tenant_isolation ON public.accounting_platforms USING ((organization_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((organization_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: accounts p_accounts_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_accounts_tenant_isolation ON public.accounts USING ((organization_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((organization_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: ai_analysis_results p_ai_analysis_results_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_ai_analysis_results_tenant_isolation ON public.ai_analysis_results USING ((organization_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((organization_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: audit_log p_audit_log_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_audit_log_tenant_isolation ON public.audit_log USING ((organization_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((organization_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: cashflow_facts_v1 p_cashflow_facts_v1_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_cashflow_facts_v1_tenant_isolation ON public.cashflow_facts_v1 USING ((organization_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((organization_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: client_assignments p_client_assignments_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_client_assignments_tenant_isolation ON public.client_assignments USING ((organization_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((organization_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: clients p_clients_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_clients_tenant_isolation ON public.clients USING ((organization_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((organization_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: document_draft_line p_document_draft_line_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_document_draft_line_tenant_isolation ON public.document_draft_line USING ((org_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((org_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: document_draft p_document_draft_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_document_draft_tenant_isolation ON public.document_draft USING ((org_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((org_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: document_inbox_item p_document_inbox_item_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_document_inbox_item_tenant_isolation ON public.document_inbox_item USING ((org_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((org_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: document_ocr_result p_document_ocr_result_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_document_ocr_result_tenant_isolation ON public.document_ocr_result USING ((org_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((org_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: ingestion_quarantine p_ingestion_quarantine_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_ingestion_quarantine_tenant_isolation ON public.ingestion_quarantine USING ((organization_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((organization_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: oauth_tokens p_oauth_tokens_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_oauth_tokens_tenant_isolation ON public.oauth_tokens USING ((platform_id IN ( SELECT accounting_platforms.id
   FROM public.accounting_platforms
  WHERE (accounting_platforms.organization_id = (current_setting('app.org_id'::text, true))::uuid)))) WITH CHECK ((platform_id IN ( SELECT accounting_platforms.id
   FROM public.accounting_platforms
  WHERE (accounting_platforms.organization_id = (current_setting('app.org_id'::text, true))::uuid))));


--
-- Name: organizations p_organizations_own_org; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_organizations_own_org ON public.organizations TO app_user, app_readonly USING ((id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: sync_history p_sync_history_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_sync_history_tenant_isolation ON public.sync_history USING ((organization_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((organization_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: transactions p_transactions_tenant_isolation; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_transactions_tenant_isolation ON public.transactions USING ((organization_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((organization_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: users p_users_same_org; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY p_users_same_org ON public.users TO app_user, app_readonly USING ((organization_id = (current_setting('app.org_id'::text, true))::uuid)) WITH CHECK ((organization_id = (current_setting('app.org_id'::text, true))::uuid));


--
-- Name: sync_history; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.sync_history ENABLE ROW LEVEL SECURITY;

--
-- Name: transactions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;

--
-- Name: users; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

--
-- PostgreSQL database dump complete
--

\unrestrict h03W5zkfcHWnhgHG5rFukbZctaDbh60hzNLcxr57AjjKq7flpl5KIRhEHdrMql3

